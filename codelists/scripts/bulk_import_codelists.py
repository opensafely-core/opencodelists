#!/usr/bin/env python

"""
Reads an file and updates/creates codelist versions

This script is intended to be run on a local machine, and will use the OpenCodelists
API to create the new codelist versions.

Run with:
    API_TOKEN=###
    python codelists/scripts/bulk_import_codelists.py
      <path/to/file>
      <path/to/config/json>
      --host # run on the specified host; defaults to localhost:7000
      --force-new-version -f  # to force a new version, even if there are no changes
      --live-run  # run for real; if not set, just reports what would be done

See additional documentation at codelists/scripts/README.md

"""

import argparse
import json
import os
import random
import string
import sys
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from django.utils.text import slugify


CODING_SYSTEMS_WITH_OLD_STYLE_CODELISTS = ["dmd", "opcs4", "readv2"]


def read_config(config_filepath):
    with config_filepath.open() as infile:
        return json.load(infile)


def main(
    filepath,
    config,
    host,
    force_new_version=False,
    force_description=False,
    force_name=False,
    force_slug=False,
    force_publish=False,
    ignore_unfound_codes=False,
    dry_run=True,
):
    if dry_run:
        print(f"############  DRY RUN ON {host}  ############")
    else:
        print(f"############  LIVE RUN ON {host}  ############")
        headers = get_headers()
    base_url = urljoin(host, f"api/v1/codelist/{config['organisation']}/")

    # Read the file and apply any aliases specified in the config
    codelists_df = process_file_to_dataframe(filepath, config)

    # Identify codelist slugs for existing codelists
    # First retrieve all codelists for this organisation
    codelists_resp = requests.get(base_url)
    if codelists_resp.status_code == 404:
        print(
            f"Could not retrieve codelists for organisation {config['organisation']}; "
            "ensure organisation slug is correct and authorised user has access to it."
        )
        sys.exit(1)
    # Create a mapping of codelist name to slug
    codelists_by_name = {
        codelist["name"]: codelist["slug"]
        for codelist in codelists_resp.json()["codelists"]
    }
    existing_slugs = [slug for slug in codelists_by_name.values()]

    # Add a codelist_slug column to the dataframe, using the codelist names from the file
    new_codelist_identifier = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=7)
    )

    def _get_slug(name, slug=None):
        # Return slug for this codelist using these rules:
        # - if an existing slug is passed then we use that
        # - if not, but the name matches an existing codelist we return that slug
        # - PCD refsets created with slugified name tags ("name-of-refset"), rather than
        #   the refset label ("refset_cod") are marked as " (obsolete)". If we can't match
        #   the name, but we can match "{name} (obsolete)", then we return the slug for that.
        #   The script (for PCD refsets) will automatically update the name.
        # - if not, but the passed slug is actually a valid slug then we return that
        # - if none of the above, we slugify the name and prefix with a unique identifier
        # Any codelist names that would produce duplicate slugs will error later when we try to create them.
        if slug and slug.lower() in existing_slugs:
            return slug.lower()
        if name in codelists_by_name:
            return codelists_by_name[name]
        if f"{name} (obsolete)" in codelists_by_name:
            return codelists_by_name[f"{name} (obsolete)"]
        if slug and slug.lower() == slugify(slug):
            return slug.lower()

        return f"{new_codelist_identifier}_{slugify(name)}"

    codelist_slugs = codelists_df.apply(
        lambda row: _get_slug(row["codelist_name"], row.get("codelist_new_slug")),
        axis=1,
    )
    codelists_df["codelist_slug"] = codelist_slugs

    # Use the slugs to identify codelists that need to be created vs those that need a new version
    distinct_codelist_slugs = set(codelists_df["codelist_slug"])
    codelists_to_create_slugs = distinct_codelist_slugs - set(
        codelists_by_name.values()
    )
    all_codelist_slugs = {
        "create": codelists_to_create_slugs,
        "update": distinct_codelist_slugs - codelists_to_create_slugs,
    }

    def get_url(action, slug):
        if action == "create":
            return base_url
        else:
            return urljoin(base_url, f"{codelist_slug}/versions/")

    codelist_count = 0
    version_count = 0
    failed_codelists = []
    failed_versions = []

    for action, codelist_slugs in all_codelist_slugs.items():
        for codelist_slug in codelist_slugs:
            # filter df to just this codelist
            df = codelists_df[codelists_df["codelist_slug"] == codelist_slug]
            assert len(set(df["coding_system"])) == 1

            codelist_name, coding_system_id, post_data = get_post_data(
                config,
                df,
                action == "create",
                force_new_version,
                force_description,
                force_name,
                force_publish,
                force_slug,
                ignore_unfound_codes,
                host,
            )

            message_part = f"new {'version for ' if action == 'update' else ''}{coding_system_id} codelist '{codelist_name}'"
            if dry_run:
                print(f"{codelist_slug}|Would create {message_part}")
                if action == "create":
                    codelist_count += 1
                else:
                    version_count += 1
            else:
                url = get_url(action, codelist_slug)
                try:
                    response = requests.post(
                        url, headers=headers, data=json.dumps(post_data)
                    )

                    if response.status_code == 200:
                        if action == "create":
                            codelist_count += 1
                        else:
                            version_count += 1
                        print(f"Created {message_part}")
                    else:
                        if action == "create":
                            failed_codelists.append((codelist_slug, url, post_data))
                        else:
                            failed_versions.append((codelist_slug, url, post_data))
                        error_message = f"Failed to create new {message_part}: {response.status_code}"
                        if (
                            response.status_code == 400
                            and not dry_run
                            and not force_new_version
                        ):
                            error_message += (
                                "\nA version with these codes may already exist. "
                                "Use -f to force creation of a new version."
                            )
                        print(error_message)
                except Exception:
                    if action == "create":
                        failed_codelists.append((codelist_slug, url, post_data))
                    else:
                        failed_versions.append((codelist_slug, url, post_data))
                    error_message = (
                        f"Failed to create new {message_part}: {response.status_code}"
                    )

    if dry_run:
        print(
            "\nDRY RUN COMPLETE\n"
            "No codelists or versions were created, but the above messages indicate what would be done.\n"
            f" - {codelist_count} new codelists would be created\n"
            f" - {version_count} existing codelists would be updated with a new version\n"
        )
    else:
        print(
            "\nSTATUS\n"
            f" - {codelist_count} new codelists successfully created\n"
            f" - {version_count} existing codelists successfully updated with a new version\n"
            f" - {len(failed_codelists)} codelists failed to be created\n"
            f" - {len(failed_versions)} existing codelists failed to be updated with a new version\n"
        )

    if failed_codelists:
        print("Failed to create the following codelists:")
        for slug, _, _ in failed_codelists:
            print(f" - Slug: {slug}")
    if failed_versions:
        print("Failed to create new versions of the following codelists:")
        for slug, _, _ in failed_versions:
            print(f" - Slug: {slug}")


def get_headers():
    token = os.environ.get("API_TOKEN")
    if token is None:
        print("API_TOKEN environment variable required.")
        sys.exit(1)
    return {"authorization": f"Token {token}"}


def process_file_to_dataframe(filepath, config):
    """
    Read a file into a Pandas dataframe and sanitise it, ready for
    importing codelists
    """
    column_names = {
        "coding_system",
        "codelist_name",
        "code",
        "term",
        "codelist_new_slug",
    }
    # Find relevant aliases from config
    codelist_name_aliases = config.get("codelist_name_aliases", {})
    column_aliases = {col: col for col in column_names}
    column_aliases.update(config.get("column_aliases", {}))

    if filepath.suffix == ".xlsx":
        # read xlsx file, ensure the code column is imported as string
        codelist_df = pd.read_excel(
            filepath,
            sheet_name=config["sheet"],
            converters={column_aliases["code"]: str},
        )
    else:
        if filepath.suffix == ".csv":
            delim = ","
        elif filepath.suffix == ".tsv":
            delim = "\t"
        elif filepath.suffix == ".txt":
            delim = config.get("delimiter", None)
            if not delim:
                raise ValueError("Delimiter must be supplied for .txt files")
        else:
            raise ValueError("Unknown file extension")
        # read text file, ensure the code column is imported as string
        codelist_df = pd.read_csv(
            filepath,
            delimiter=delim,
            converters={column_aliases["code"]: str},
        )

    if config.get("limit_to_named_codelists", False):
        # if necessary, limit to only the named columns
        codelist_name_col = codelist_df[
            config["column_aliases"].get("codelist_name", "codelist_name")
        ]
        codelist_df = codelist_df[codelist_name_col.isin(codelist_name_aliases.keys())]

    # Rename df columns with any aliased column names
    codelist_df.rename(columns={v: k for k, v in column_aliases.items()}, inplace=True)

    # Set coding system column where not present and only one configured
    if "coding_system" not in codelist_df.columns:
        if len(config["coding_systems"]) > 1:
            raise ValueError(
                "coding_system column must be present when multiple coding systems configured"
            )
        else:
            codelist_df["coding_system"] = list(config["coding_systems"].keys())[0]

    relevant_df_columns = set(codelist_df.columns) & column_names
    required_columns = column_names - {"term", "codelist_new_slug"}
    for column in required_columns:
        # ensure all required columns are now present
        assert column in relevant_df_columns, f"Expected column {column} not found"

    # update the codelist name column with any aliases
    def update_name(name):
        return codelist_name_aliases.get(name, name)

    aliased_names = codelist_df["codelist_name"].apply(update_name)
    codelist_df["codelist_name"] = aliased_names

    # Remove extraneous whitespace from all columns of interest
    for column in relevant_df_columns:
        codelist_df[column] = codelist_df[column].str.strip()

    return codelist_df


def get_post_data(
    config,
    codelist_df,
    create_new_codelist,
    force_new_version,
    force_description,
    force_name,
    force_publish,
    force_slug,
    ignore_unfound_codes,
    host,
):
    """
    Return the relevant data to post to the api endpoint to create a new
    codelist or codelist version
    """
    first_row = codelist_df.iloc[0]
    codelist_name = first_row["codelist_name"]
    coding_system_from_data = first_row["coding_system"]
    coding_system_id = config["coding_systems"][coding_system_from_data]["id"]
    release_db_alias = config["coding_systems"][coding_system_from_data]["release"]

    # In dev mode you might not have the coding system db installed which causes 500
    # errors. For better developer experience, if running against localhost we check
    # that the db exists and is not empty before proceeding. Also ensure the TEST_IN_DOCKER var
    # is not set as the docker environment doesn't have the dbs installed either, but
    # we don't want to block the CI tests.
    if "localhost" in host and not os.environ.get("TEST_IN_DOCKER"):
        db_path = (
            Path(__file__).resolve().parent.parent.parent
            / "coding_systems"
            / coding_system_id
            / f"{release_db_alias}.sqlite3"
        )
        # check file exists and is not an empty sqlite3 file e.g. larger than 4096 bytes (but
        # let's do 100kb to be sure e.g. the test snomed db is 300kb)
        if not db_path.exists() or db_path.stat().st_size < 100_000:
            print(
                f"\n\nYou're running against localhost, but I don't think you have the "
                f"correct coding system database. Please check that the db exists at:\n\n"
                f"  {db_path}\n\nNB - it might exist but be empty if it's < 100KB in size "
                "so you may still need to download it - or change the config to use a different db.\n"
            )
            sys.exit(1)

    tag = config.get("tag")
    description = first_row.get("codelist_description", None)
    if "description_template" in config:
        description = config["description_template"] % description

    post_data = {"coding_system_database_alias": release_db_alias, "tag": tag}
    if coding_system_id in CODING_SYSTEMS_WITH_OLD_STYLE_CODELISTS:
        # create an old-style codelist/version with csv_data
        post_data["csv_data"] = codelist_df[["code", "term"]].to_csv()
    else:
        post_data.update(
            {
                "always_create_new_version": force_new_version,
                "codes": list(set(codelist_df["code"])),
            }
        )

    if create_new_codelist:
        post_data.update(
            {
                "name": codelist_name,
                "coding_system_id": coding_system_id,
                "description": description,
                "methodology": None,
            }
        )

    if force_description:
        post_data["description"] = description
    if force_name:
        post_data["name"] = codelist_name
    if force_publish:
        post_data["should_publish"] = True
    if force_slug:
        post_data["new_slug"] = first_row["codelist_new_slug"].lower()
    if ignore_unfound_codes:
        post_data["ignore_unfound_codes"] = True

    return codelist_name, coding_system_id, post_data


class ValidateHost(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values != "bar":
            parser.error(f"Please enter a valid. Got: {values}")
        setattr(namespace, self.dest, values)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("file_path", type=Path, help="Path/to/file")
    parser.add_argument("config_file", type=Path, help="Path/to/config/json/file")
    parser.add_argument(
        "--force-new-version",
        "-f",
        action="store_true",
        help="Always create a new version, even if a version with identical codes already exists.",
    )
    parser.add_argument(
        "--force-description",
        action="store_true",
        help="Always update the description, even if it already exists.",
    )
    parser.add_argument(
        "--force-name",
        action="store_true",
        help="Always update the name, even if it already exists.",
    )
    parser.add_argument(
        "--force-publish",
        action="store_true",
        help="For new versions, this causes them to auto-publish rather than defaulting to under review.",
    )
    parser.add_argument(
        "--force-slug",
        action="store_true",
        help="For new codelists, user the provided slug rather than generating one.",
    )
    parser.add_argument(
        "--ignore-unfound-codes",
        action="store_true",
        help=(
            "If set, will force the creation of codelists even if the codes "
            "aren't found in the coding system. This is useful if e.g. you "
            "are importing the PCD refsets which occasionally contain codes "
            "from the clinical AND medication SNOMED dictionaries. This causes "
            "unfound codes to be ignored, but appends the ignored codes to the description."
        ),
    )
    parser.add_argument(
        "--live-run",
        action="store_true",
        help=(
            "Run this command for real; if not specified, this will be a dry run that reports "
            "codelists/versions that will be created but does not actually do anything."
        ),
    )
    parser.add_argument(
        "--host",
        default="http://localhost:7000",
        help="Host to use for API calls; https://www.opencodelists.org for live prod run",
    )

    arguments = parser.parse_args()
    config = read_config(arguments.config_file)

    return (
        arguments.file_path,
        config,
        arguments.host,
        arguments.force_new_version,
        arguments.force_description,
        arguments.force_name,
        arguments.force_publish,
        arguments.force_slug,
        arguments.ignore_unfound_codes,
        not arguments.live_run,
    )


if __name__ == "__main__":
    main(*parse_args())
