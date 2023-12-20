#!/usr/bin/env python

"""
Reads an XLSX file and updates/creates codelist versions

This script is intended to be run on a local machine, and will use the OpenCodelists
API to create the new codelist versions.

Create a token on the server with:
    from rest_framework.authtoken.models import Token
    token = Token.objects.create(user=...)
    print(user.api_token)

Run with:
    API_TOKEN=###
    python codelists/scripts/import_codelists_from_xlsx.py
      <path/to/xlsx>
      <path/to/config/json>
      --host # run on the specified host; defaults to localhost:7000
      --force-new-version -f  # to force a new version, even if there are no changes
      --live-run  # run for real; if not set, just reports what would be done

(NOTE: when running on prod use --host https://www.opensafely.org; if run with https://opensafely.org, the
redirect to www will make the api calls return 405s.)

Provide a path to an xlsx file, which should contain at least one sheet, with at least columns:
 - coding_system
 - codelist_name
 - code
 - term (only required if file includes dm+d codelists)

 Each row represents one code in one codelist version, e.g. the following represents
 one SNOMED-CT codelist and one dm+d codelist, each with 3 codes.

 coding_system | codelist_name | code
 --------------|---------------|-----
 snomedct      | Asthma        | 1234
 snomedct      | Asthma        | 2345
 snomedct      | Asthma        | 3456
 dmd           | Paracetemol   | ABCD
 dmd           | Paracetemol   | BCDE
 dmd           | Paracetemol   | CDEF

Note the columns names, coding system refs and codelist names can be aliased
in the config file, see below.

Provide a config file in json format:
required keys:
- organisation (Organisation slug)
- sheet (sheet in the workbook that contains the list of codes)
- coding_systems (for each coding system value present in the workbook,
  the id of the coding system in OpenCodelists and the database alias of the
  release to be used for the new codelist. In the example below, the coding
  system column in the xlsx file  contains values "SNOMED CT" and "dm+d")
optional keys:
- tag (optional tag for the codelist versions)
- column_aliases (optional aliases for column names. We expect columns named
  coding_system, codelist_name, code, term (optional); column aliases is a dict
  mapping one or more of these column names to the actual name in the xlsx file.)
- codelist_name_aliases (in case the the name
  in OpenCodelists doesn't exactly match the value in the codelist_name column.
  Dict mapping from the name in the xlsx file (key) to name in OpenCodelists (value)

example_config.json:
{
    "organisation": "pincer",
    "sheet": "SCT codeclusters",
    "coding_systems": {
        "SNOMED CT": {
            "id": "snomedct",
            "release": "snomedct_3600_20230419"
        },
        "dm+d": {
            "id": "dmd",
            "release": "dmd_2023-530_20230522"
        }
    },
    "tag": "v2.0",
    "column_aliases": {
        "coding_system": "Coding_scheme",
        "codelist_name": "Cluster_description",
        "code": "SNOMED code"
        "term": "SNOMED_Description",
    },
    "codelist_name_aliases": {
        "Loop diuretics": "Loop diuretics Rx",
        "Lithium medication": "Lithium Rx",
        "Methrotrexate": "Methotrexate Rx",
        "NSAID medication": "oral NSAID Rx",
        "Non Aspirin antiplatelet": "Antiplatelet Rx without aspirin Rx",
        "Non Selective Beta Blockers": "Non cardio-selective beta-blocker Rx",
        "Aspirin & other antiplatelets": "aspirin + other antiplatelet Rx",
        "PPIs and H2 blockers": "Ulcer healing drugs: PPI & H2 blockers Rx"
    }
}

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
    xlsx_filepath,
    config,
    host,
    force_new_version=False,
    dry_run=True,
):
    if dry_run:
        print(f"############  DRY RUN ON {host}  ############")

    headers = get_headers()
    base_url = urljoin(host, f"api/v1/codelist/{config['organisation']}/")

    # Read the xlsx file and apply any aliases specified in the config
    codelists_df = process_xlsx_to_dataframe(xlsx_filepath, config)

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
    # Add a codelist_slug column to the dataframe, using the codelist names from the xlsx file
    new_codelist_identifier = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=7)
    )

    def _get_slug(name):
        # return slug from name for this codelist, or if not found, prefix with
        # new_codelist_identifier to ensure it's unique. Any codelist names that would
        # produce duplicate slugs will error later when we try to create them.
        return codelists_by_name.get(name, f"{new_codelist_identifier}_{slugify(name)}")

    codelist_slugs = codelists_df["codelist_name"].apply(_get_slug)
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

    for action, codelist_slugs in all_codelist_slugs.items():
        for codelist_slug in codelist_slugs:
            # filter df to just this codelist
            df = codelists_df[codelists_df["codelist_slug"] == codelist_slug]
            assert len(set(df["coding_system"])) == 1

            codelist_name, coding_system_id, post_data = get_post_data(
                config, df, action == "create", force_new_version
            )

            message_part = f"new {'version for ' if action == 'update' else ''}{coding_system_id} codelist '{codelist_name}'"
            if dry_run:
                print(f"Would create {message_part}")
            else:
                url = get_url(action, codelist_slug)
                response = requests.post(
                    url, headers=headers, data=json.dumps(post_data)
                )

                if response.status_code == 200:
                    print(f"Created {message_part}")
                else:
                    error_message = (
                        f"Failed to create new {message_part}: {response.status_code}"
                    )
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


def get_headers():
    token = os.environ.get("API_TOKEN")
    if token is None:
        print("API_TOKEN environment variable required.")
        sys.exit(1)
    return {"authorization": f"Token {token}"}


def process_xlsx_to_dataframe(xlsx_filepath, config):
    """
    Read an xlsx file into a Pandas dataframe and santitise it, ready for
    importing codelists
    """
    column_names = {"coding_system", "codelist_name", "code", "term"}
    # Find relevant aliases from config
    codelist_name_aliases = config.get("codelist_name_aliases", {})
    column_aliases = {col: col for col in column_names}
    column_aliases.update(config.get("column_aliases", {}))

    # read xlsx file, ensure the code column is imported as string
    codelist_df = pd.read_excel(
        xlsx_filepath,
        sheet_name=config["sheet"],
        converters={column_aliases["code"]: str},
    )
    # Rename df columns with any aliased column names
    codelist_df.rename(columns={v: k for k, v in column_aliases.items()}, inplace=True)

    relevant_df_columns = set(codelist_df.columns) & column_names
    required_columns = column_names - {"term"}
    for column in required_columns:
        # ensure all required columns are now present
        assert column in relevant_df_columns, f"Expected column {column} not found"

    # Remove extraneous whitespace from all columns of interest
    for column in relevant_df_columns:
        codelist_df[column] = codelist_df[column].str.strip()

    # update the codelist name column with any aliases
    def update_name(name):
        return codelist_name_aliases.get(name, name)

    aliased_names = codelist_df["codelist_name"].apply(update_name)
    codelist_df["codelist_name"] = aliased_names

    return codelist_df


def get_post_data(config, codelist_df, create_new_codelist, force_new_version):
    """
    Return the relevant data to post to the api endpoint to create a new
    codelist or codelist version
    """
    first_row = codelist_df.iloc[0]
    codelist_name = first_row["codelist_name"]
    coding_system_from_data = first_row["coding_system"]
    coding_system_id = config["coding_systems"][coding_system_from_data]["id"]
    release_db_alias = config["coding_systems"][coding_system_from_data]["release"]
    tag = config.get("tag")

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
                "description": None,
                "methodology": None,
            }
        )

    return codelist_name, coding_system_id, post_data


class ValidateHost(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values != "bar":
            parser.error(f"Please enter a valid. Got: {values}")
        setattr(namespace, self.dest, values)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("xlsx_file", type=Path, help="Path/to/xlsx/file")
    parser.add_argument("config_file", type=Path, help="Path/to/config/json/file")
    parser.add_argument(
        "--force-new-version",
        "-f",
        action="store_true",
        help="Always create a new version, even if a version with identical codes already exists.",
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
        help="Host to use for API calls; https://www.opensafely.org for live prod run",
    )

    arguments = parser.parse_args()
    config = read_config(arguments.config_file)

    return (
        arguments.xlsx_file,
        config,
        arguments.host,
        arguments.force_new_version,
        not arguments.live_run,
    )


if __name__ == "__main__":
    main(*parse_args())
