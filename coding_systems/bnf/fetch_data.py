"""Fetch the latest BNF coding system release from the NHSBSA Open Data Portal (ODP) API.

This module handles fetching the release CSV from the ODP API and is
used by the `fetch_bnf_data` Django management command.

The `import_data.py` module handles importing the associated metadata
into the core database and loading the release data into a newly created
coding system release database.

In this module, the script entry point is `fetch_data`.
`csv_directory` is the directory containing existing BNF release
CSVs and the destination for newly-downloaded CSVs.

This script:

1. finds the latest BNF release CSV stored locally;
2. fetches the current year's release metadata from the NHSBSA ODP API;
3. compares the latest local and ODP releases; and
4. downloads the latest CSV when the local data is missing or out of date.

To execute the script, run:

`dokku run opencodelists python manage.py fetch_bnf_data /storage/data/bnf`

BNF current year release information is available from:
https://opendata.nhsbsa.net/dataset/bnf-code-information-current-year
"""

import logging
import re
from pathlib import Path

import requests
from requests.exceptions import RequestException


log = logging.getLogger(__name__)


def fetch_data(csv_directory: Path) -> Path | None:
    """
    Download the latest BNF coding system release CSV from the NHSBSA
    ODP API if it is not already available locally.

    Returns the path to the downloaded CSV, or None if the local
    release is already up to date.
    """

    csv_path = find_latest_local_csv(csv_directory)

    odp_response = get_all_releases()

    # Get metadata for the latest BNF coding system release, using
    # the release date and version from the resource name rather than ODP's
    # resource ordering, so "latest" is defined by the BNF release itself.
    latest = max(
        odp_response["result"]["resources"],
        key=lambda resource: parse_name(resource["name"]),
    )
    name = latest["name"]
    url = latest["url"]
    date, version = parse_name(name)

    if csv_path is not None and have_latest_csv(
        date,
        version,
        csv_path,
    ):
        log.info("Latest BNF release CSV file already exists locally: %s.", csv_path)
        return None

    log.info("New BNF release available: %s.", name)
    new_csv_path = download_csv(
        date,
        version,
        url,
        csv_directory,
    )

    return new_csv_path


def parse_name(name):
    """Given a BNF release name or filename, extract the release date and version.

    Supports:
    - Legacy CSV filenames, e.g. `bnf_code_202412_version_86.csv`.
    - Current CSV filenames, e.g. `bnf_code_current_202608_version_90.csv`.
    - ODP release names, e.g. `BNF_CODE_CURRENT_202608_VERSION_90`.
    - ODP release names with a `_FINAL` suffix, as used in August 2025.

    Returns a tuple of `(date, version)`, where date is a `str` in YYYYMM
    format and version is an `int`.

    For example:
        >>> date, version = parse_name("bnf_code_current_202608_version_90.csv")
        >>> date
        '202608'
        >>> version
        90
    """

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
        log.debug("Fetching ODP metadata for the current year's BNF releases...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        e.add_note("Failed to fetch the current year's BNF release metadata from ODP")
        raise


def find_latest_local_csv(csv_directory: Path):
    """Given a directory containing BNF coding system release CSVs,
    return the path to the latest release, or `None` if no releases exist."""
    existing_files = csv_directory.glob("*.csv")

    latest_csv_path = max(
        existing_files,
        default=None,
        key=lambda file: parse_name(file.name),
    )

    return latest_csv_path


def have_latest_csv(latest_date, latest_version, latest_bnf_release_csv_path):
    """Determine whether the latest local BNF release CSV we have on
    disk is the latest release available from the ODP API."""
    csv_date, csv_version = parse_name(latest_bnf_release_csv_path.name)

    return csv_date == latest_date and csv_version == latest_version


def download_csv(date, version, url, csv_directory: Path):
    """
    Download the latest BNF coding system release CSV from the NHSBSA ODP API.

    `csv_directory` is the directory containing existing BNF release CSVs
    and the destination for newly-downloaded CSVs.

    Returns the Path of the downloaded CSV file.
    """
    filename = f"bnf_code_current_{date}_version_{version}.csv"
    download_path = csv_directory / filename

    try:
        with requests.get(
            url,
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
