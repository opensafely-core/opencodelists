#!/usr/bin/env python

"""
Django Script to automatically update NHS Primary Care Domain Refsets

These are released whenever they are updated i.e. not on a particular release cycle. There
are roughly 4 a year. This script allows them to be loaded into opencodelists, as either new
versions of existing codelists, or new codelists if they don't yet exist.

This script:
1. Fetches available releases from TRUD API
2. Identifies releases the same or newer than the current one
3. Downloads and extracts a particular release
4. Optionally filters to specific Cluster_IDs (refset IDs) if provided
5. Updates the configuration JSON with the new release date (if --live-run is set)
6. Runs the bulk import process with the new files

The bulk import process will tell you how many success/failures there were. It is worth
trying to rerun the script for any failed imports (assuming there aren't that many). See
below for how to run just for a few cluster ids.

This script requires a TRUD_API_KEY env var to either be set or defined in your .env file.

You must also be a member of the "NHSD Primary Care Domain Refsets" organisation on
opencodelists, and have an API_TOKEN set up via the admin interface.

Usage:
    just manage "runscript update_pcd_refsets --script-args='[--live-run] [--host=xxx] [REFSET_ID [REFSET_ID ...]]'"

Flags:
    --live-run      Actually update the config and run the bulk import for real (not a dry run).
                    If not set, the script will perform a dry run and not update the config.
    --host          Base URL for the API (default: http://localhost:7000) but likely
                    https://www.opencodelists.org/ for the live run

Arguments:
    REFSET_ID       Optional space-separated list of Cluster_IDs (refset IDs) to include in the output CSV.
                    If omitted, all clusters are included.

Examples:
    # Dry run, process only specific clusters
    just manage "runscript update_pcd_refsets --script-args='ANTIPSYONLYDRUG_COD C19ACTIVITY_COD'"

    # Live run, production host, process all clusters
    just manage "runscript update_pcd_refsets --script-args='--live-run --host=https://www.opencodelists.org/'"


"""

import csv
import json
import os
import re
import shlex
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZipFile

import requests

from coding_systems.base.trud_utils import TrudDownloader


CONFIG_FILE = Path(__file__).parent / "nhsd_primary_care_refsets.json"
CLUSTER_REFSET_PATTERN = r"GPData_Cluster_Refset_1000230_\d+\.csv"


class Downloader(TrudDownloader):
    item_number = 659
    release_regex = re.compile(r"(?P<release>uk_sct2pc_\d+\.\d+\.\d+_\d{8})")

    def get_release_name_from_release_metadata(self, release_metadata):
        return release_metadata["release"][-8:]


def get_tag_and_coding_system(config_file):
    """Return the 'tag' and the first key from 'coding_systems' in the config file."""
    print(f"\nReading config file ({config_file}):")
    with open(config_file) as f:
        config = json.load(f)
    tag = config.get("tag")
    coding_systems = config.get("coding_systems", {})
    first_coding_system = next(iter(coding_systems), None)
    print(f" - Current tag: {tag}")
    print(f" - Coding system: {first_coding_system}")
    return tag, first_coding_system


def fetch_pcd_releases(downloader, current_tag):
    """
    Fetch available releases from TRUD API, filter to those the same or newer
    than the current tag, and return the tag, id, date, and url.
    The "releases" array from TRUD looks like:
    {
      "id": "'uk_sct2pc_56.0.0_20250627000000Z.zip',
      "releaseDate": "2025-06-30",
      "archiveFileUrl": "https://isd.digital.nhs.uk/.../uk_sct2pc_56.0.0_20250627000000Z.zip"
      ...
    }
    """
    msg = "\nFetching available releases..."
    if current_tag:
        msg += f" (the same or newer than the current tag: {current_tag})"
    print(msg)
    releases = [
        release_metadata
        for release in downloader.get_releases()
        if (release_metadata := downloader.get_release_metadata(release))
        and release_metadata["release_name"] >= current_tag
    ]
    releases.sort(key=lambda r: r["release_name"], reverse=True)

    print(f" - Found {len(releases)} releases")
    return releases


def download_and_extract(downloader, release):
    """Download and extract the archive from the given URL."""
    print("\nDownload and extracting zip from TRUD:")
    release_zipfile = downloader.download_release(
        release["release_name"], release["valid_from"], False
    )
    try:
        with ZipFile(release_zipfile) as zip_file:
            print(" - Extracting archive...")
            zip_file.extractall(downloader.release_dir)

            # Find the cluster refset CSV file
            cluster_files = []
            for root, _, files in os.walk(downloader.release_dir):
                for file in files:
                    if re.match(CLUSTER_REFSET_PATTERN, file):
                        cluster_files.append(os.path.join(root, file))

            if not cluster_files:
                raise FileNotFoundError(
                    "No cluster refset CSV file found in the archive"
                )

            assert len(cluster_files) == 1, (
                "Multiple cluster refset CSV files found - which is unexpected"
            )
            print(f" - Extracted cluster file: {cluster_files[0]}")
            return cluster_files[0]
    finally:
        os.unlink(release_zipfile)


def get_latest_db_release_from_api(base_url, coding_system_id):
    """
    Fetch the latest available database release for the coding system from the API.
    Returns the database_alias string (e.g., 'snomedct_4000_20250416') or None.
    """
    url = f"{base_url}/coding-systems/latest-releases?type=json"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        if coding_system_id in data and "database_alias" in data[coding_system_id]:
            return data[coding_system_id]["database_alias"]
        else:
            print(f"No database_alias found for {coding_system_id} in API response.")
            return None
    except Exception as e:
        print(f"Error fetching latest DB release from API: {e}")
        return None


def update_config_file(config_file, base_url, new_tag, coding_system_id):
    """Update the config file with the new tag and database release."""
    with open(config_file) as f:
        config = json.load(f)

    config["tag"] = new_tag

    db_release = get_latest_db_release_from_api(base_url, coding_system_id)

    # Update the coding system release
    if (
        db_release
        and "coding_systems" in config
        and coding_system_id in config["coding_systems"]
    ):
        config["coding_systems"][coding_system_id]["release"] = db_release

    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)
        f.write("\n")

    print(f"\nUpdated config file with new tag: {new_tag}\n")


def parse_args(args):
    import argparse

    parser = argparse.ArgumentParser(
        description="Update NHS Primary Care Domain Refsets"
    )
    parser.add_argument(
        "--live-run",
        action="store_true",
        help="If set, update config and run bulk import for real (not a dry run)",
    )
    parser.add_argument(
        "--host",
        default="http://localhost:7000",
        help="Base URL for the API (default: http://localhost:7000)",
    )
    parser.add_argument(
        "names",
        nargs="*",
        help="Optional list of Cluster_IDs to include in the output CSV. If omitted, all are included.",
    )
    return parser.parse_args(shlex.split(args[0]) if args else [])


def run_bulk_import(cluster_file, config_file, host, release, live_run, names=None):
    """Run the bulk import script with the extracted file."""
    bulk_import_script = Path(__file__).parent / "bulk_import_codelists.py"

    if not os.environ.get("API_TOKEN"):
        print(
            "Warning: API_TOKEN environment variable not set. Import will be a dry run. "
            "Rerun the command prefixed with:\n"
            "         API_TOKEN=xxx <existing command>\n"
            "         to pass the API_TOKEN.\n"
            "NB the API_TOKEN is for connecting to the opencodelists API (either locally "
            "or in production. The TRUD_API_KEY is different, and is what is needed to get "
            "the PCD refset files from TRUD."
        )
        live_run = False

    cmd = [
        "python3",
        str(bulk_import_script),
        str(cluster_file),
        str(config_file),
        "--host",
        host,
    ]
    if live_run:
        cmd.append("--live-run")
        cmd.append("--force-new-version")
        cmd.append("--force-description")
        cmd.append("--force-name")
        cmd.append("--force-slug")
        cmd.append("--force-publish")
        cmd.append("--ignore-unfound-codes")

    # Prompt user for confirmation
    print("\nAbout to process the following release:")
    print(f"  Release ID: {release['release']}")
    print(f"  Tag: {release['release_name']}")
    if names:
        print(f"  Filtering to Cluster_IDs: {', '.join(names)}")
    else:
        print("  Including ALL Cluster_IDs.")
    print(f"  This will be a {f'LIVE RUN against {host}' if live_run else 'DRY RUN'}")
    proceed = input("Proceed? [Y/n]: ").strip().lower()
    if proceed not in ("", "y", "yes"):
        print("Aborted.")
        return

    print(f"Running bulk import: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def process_cluster_file(input_file, output_file, names=None):
    """
    Process the cluster file to extract only the needed columns and handle encoding issues.
    Optionally filter to only rows where Cluster_ID is in names (case-insensitive).
    Returns the number of rows written.
    """
    print(f"\nProcessing {input_file} to extract required columns...")

    names_lower = set(n.lower() for n in names) if names else None

    # The csv files are typically encoded with "Windows 1252" format, but adding fallbacks
    # here in case it changes
    encodings = ["cp1252", "utf-8", "latin-1", "iso-8859-1"]
    for encoding in encodings:
        try:
            with (
                open(input_file, encoding=encoding, newline="") as infile,
                open(output_file, "w", encoding="utf-8", newline="") as outfile,
            ):
                reader = csv.DictReader(infile)
                fieldnames = [
                    "Cluster_Desc",
                    "ConceptId",
                    "ConceptId_Description",
                    "Cluster_ID",
                    "Cluster_Slug",
                ]
                writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=",")
                writer.writeheader()
                row_count = 0
                for row in reader:
                    cluster_id = row.get("Cluster_ID", "")
                    # Active_in_Refset is used to "retire" codes from a refset. These codes were
                    # incorrectly included in the past so we should ignore them. NB this is
                    # separate to "inactive" SNOMED codes. Refsets can contain "inactive" codes
                    # (which is in the unused Active_Code_Status field in this csv) and we want to
                    # include those because analyses may well involve a time when these codes were active.
                    # The possible "Type_of_Inclusion" values are "PC refset" for the primary care (clinical)
                    # ones, and "Refset" for the drug refsets. We currently only import the clinical ones.
                    if (
                        row.get("Active_in_Refset") == "1"
                        and row.get("Type_of_Inclusion") == "PC refset"
                        and (not names_lower or cluster_id.lower() in names_lower)
                    ):
                        new_row = {
                            "Cluster_Desc": row.get("Cluster_Desc", ""),
                            "ConceptId": row.get("ConceptId", ""),
                            "ConceptId_Description": row.get(
                                "ConceptId_Description", ""
                            ),
                            "Cluster_ID": cluster_id,
                            "Cluster_Slug": cluster_id,
                        }
                        writer.writerow(new_row)
                        row_count += 1
                print(
                    f" - Successfully processed file using {encoding} encoding. {row_count} rows written to {output_file}"
                )
                return output_file, row_count
        except UnicodeDecodeError:
            print(f"Failed to decode with {encoding}, trying next encoding...")
    raise ValueError(
        f"Could not process file {input_file} with any of the tried encodings"
    )


def get_user_choice_for_release(releases, current_tag):
    print("\nPlease select which release you want to import:")
    for i, release in enumerate(releases):
        msg = f" [{i + 1}] {release['release']} (Release date: {release['valid_from']}, Tag: {release['release_name']})"
        if release["release_name"] == current_tag:
            msg += "   <-- CURRENT TAG"
        print(msg)

    while True:
        try:
            choice = input(
                f"Select a release to use {f'[1-{len(releases)}] ' if len(releases) > 1 else ''}(default: 1): "
            )
            if not choice:
                choice = 1
            else:
                choice = int(choice)

            if 1 <= choice <= len(releases):
                release_to_use = releases[choice - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(releases)}")
        except ValueError:
            print("Please enter a valid number")

    print(
        f"Processing release: {release_to_use['release']} (tag: {release_to_use['release_name']})"
    )
    return release_to_use


def run(*args):
    args = parse_args(args)
    # Get current tag from config
    current_tag, coding_system_id = get_tag_and_coding_system(CONFIG_FILE)

    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        downloader = Downloader(temp_dir)
        # Fetch possible new releases
        releases = fetch_pcd_releases(downloader, current_tag)

        if not releases:
            print(
                f"No releases found. The current version ({current_tag}) is newer "
                "than all releases available from the TRUD api. Something's gone "
                "wrong because you should always at least match the latest tag."
            )
            exit(0)

        release_to_use = get_user_choice_for_release(releases, current_tag)

        # Download and extract
        cluster_file = download_and_extract(downloader, release_to_use)

        # Process the file to extract only the columns we need
        processed_filename = f"processed_{os.path.basename(cluster_file)}"
        target_file = Path(temp_dir) / processed_filename
        processed_file, row_count = process_cluster_file(
            cluster_file, target_file, names=args.names
        )
        if row_count == 0:
            print("\nNo rows matched the filter. Skipping bulk import.")
            return
        # Only update config and pass --live-run if requested
        if args.live_run:
            update_config_file(
                CONFIG_FILE, args.host, release_to_use["release_name"], coding_system_id
            )
        else:
            print("\nDry run: not updating config file and not running live import.\n")

        run_bulk_import(
            processed_file,
            CONFIG_FILE,
            args.host,
            release_to_use,
            live_run=args.live_run,
            names=args.names,
        )
