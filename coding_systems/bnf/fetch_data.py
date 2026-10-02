"""Fetch the latest BNF coding system release from the NHSBSA Open Data Portal (ODP) API.

This module contains the data-fetching script run by the
`fetch_bnf_data` Django management command.

The script entry point is `fetch_data`, which:

1. finds the latest BNF release CSV stored locally;
2. fetches the current year's release metadata from the NHSBSA ODP API;
3. compares the latest local and ODP releases; and
4. downloads the latest CSV when the local data is missing or out of date.

To execute the script, run:

`dokku run opencodelists python manage.py fetch_bnf_data /storage/data`

BNF current year release information is available from:
https://opendata.nhsbsa.net/dataset/bnf-code-information-current-year
"""

import logging
import re
from collections import namedtuple
from pathlib import Path

import requests
from requests.exceptions import RequestException


log = logging.getLogger(__name__)


BNFReleaseInfo = namedtuple(
    "BNFReleaseInfo",
    ["name", "date", "version", "url"],
)


def fetch_data(directory: str) -> Path | None:
    """
    Download the latest BNF coding system release CSV from the NHSBSA
    ODP API if it is not already available locally.

    Returns the path to the downloaded CSV, or None if the local
    release is already up to date.
    """

    bnf_data_dir = Path(directory) / "bnf"

    csv_path = find_latest_local_csv(bnf_data_dir)

    odp_response = get_all_releases()

    latest_release_info = find_latest_release(odp_response)

    if csv_path is not None and have_latest_csv(
        latest_release_info,
        csv_path,
    ):
        log.debug("BNF release already up to date")
        return None

    log.info("New BNF release available: %s.", latest_release_info.name)
    new_csv_path = download_csv(
        latest_release_info,
        bnf_data_dir,
    )

    return new_csv_path


def parse_name(name):
    """Given a BNF release name or filename, extract the release date and version."""

    # BNF CSVs use legacy (`bnf_code_202608_version_90.csv`) and
    # current (`bnf_code_current_202503_version_88.csv`) naming conventions.
    # ODP release names use the format `BNF_CODE_CURRENT_202608_VERSION_90';
    # the August 2025 release appended `_FINAL`.
    match = re.match(
        r"^BNF_CODE_(?:CURRENT_)?(\d{6})_VERSION_(\d+)(?:_FINAL)?(?:\.csv)?$",
        name,
        re.IGNORECASE,
    )

    if match is None:
        raise ValueError(f"Unexpected BNF release name: {name}")

    date = match.group(1)
    version = int(match.group(2))

    return date, version


def get_all_releases():
    """
    Get metadata for all BNF coding system releases published in the
    current calendar year (Jan to Dec) from the NHSBSA ODP API.

    Returns a dict containing deserialized ODP API response data.
    """
    url = "https://opendata.nhsbsa.net/api/3/action/package_show?id=bnf-code-information-current-year"
    try:
        log.debug("Fetching ODP metadata for all BNF coding system releases...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        current_year = response.json()
        return current_year
    except RequestException as e:
        e.add_note("Failed to fetch the latest BNF release information from ODP")
        raise


def find_latest_release(response_data):
    """
    Get metadata for the latest BNF coding system release.

    Returns a BNFReleaseInfo containing the name, date, version, and
    CSV download URL for the latest available BNF coding system release.
    """

    # Use the release date and version from the resource name rather than ODP's
    # resource ordering, so "latest" is defined by the BNF release itself.
    latest = max(
        response_data["result"]["resources"],
        key=lambda resource: parse_name(resource["name"]),
    )

    name = latest["name"]

    url = latest["url"]

    date, version = parse_name(name)

    return BNFReleaseInfo(
        date=date,
        name=name,
        url=url,
        version=version,
    )


def find_latest_local_csv(directory: Path):
    """Given a directory containing BNF coding system release CSVs,
    return the path to the latest release, or `None` if no releases exist."""
    existing_files = directory.glob("*.csv")

    latest_csv_path = max(
        existing_files,
        default=None,
        key=lambda file: parse_name(file.name),
    )

    return latest_csv_path


def have_latest_csv(latest_bnf_release_info, latest_bnf_release_csv_path):
    """Determine whether the latest local BNF release CSV we have on
    disk is the latest release available from the ODP API."""
    csv_date, csv_version = parse_name(latest_bnf_release_csv_path.name)

    return (
        csv_date == latest_bnf_release_info.date
        and csv_version == latest_bnf_release_info.version
    )


def download_csv(latest_bnf_release, download_directory: Path):
    """
    Download the latest BNF coding system release CSV from the NHSBSA ODP API.

    Returns the Path of the downloaded CSV file.
    """
    filename = (
        f"bnf_code_current_{latest_bnf_release.date}"
        f"_version_{latest_bnf_release.version}.csv"
    )
    download_path = download_directory / filename

    try:
        with requests.get(
            latest_bnf_release.url,
            stream=True,
            timeout=10,
        ) as response:
            response.raise_for_status()

            with download_path.open("wb") as f:
                log.info("Downloading the latest BNF release CSV...")
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
    except RequestException as e:
        e.add_note("Failed to download the latest BNF release CSV from ODP")
        raise

    log.info("Downloaded BNF release to: %s", download_path)
    return download_path
