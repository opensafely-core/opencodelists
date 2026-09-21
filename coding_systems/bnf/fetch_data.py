import re
from collections import namedtuple

import requests
from requests.exceptions import RequestException


BNFReleaseInfo = namedtuple(
    "BNFReleaseInfo",
    ["name", "date", "version", "url"],
)


# Find the latest BNF coding-system release published by ODP.
def get_current_year_bnf_releases_info():
    """
    Get metadata for all BNF coding system releases published in the current calendar year (Jan to Dec) from the NHSBSA ODP API.

    Returns the HTTP response from the NHSBSA ODP API.
    """
    url = "https://opendata.nhsbsa.net/api/3/action/package_show?id=bnf-code-information-current-year"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response
    except RequestException as e:
        e.add_note("Failed to fetch the latest BNF release information from ODP")
        raise


def get_latest_bnf_release_info(response):
    """
    Get metadata for the latest BNF coding system release.

    Returns a BNFReleaseInfo containing the name, date, version, and CSV download URL for the latest available BNF coding system release.
    """

    latest_bnf_release_info = response.json()["result"]["resources"][-1]

    # As of March 2025, release names are formatted as follows: 'BNF_CODE_CURRENT_202608_VERSION_90'
    name = latest_bnf_release_info["name"]

    url = latest_bnf_release_info["url"]

    # BNF CSV files are named e.g. bnf_code_current_202503_version_88.csv.
    # Get the date and the version of the latest release, so we can
    # check these against CSV filenames we already have later
    match = re.match(r"^BNF_CODE_CURRENT_(\d{6})_VERSION_(\d+)(_FINAL)?$", name)

    date = match.group(1)
    version = match.group(2)

    return BNFReleaseInfo(
        date=date,
        name=name,
        url=url,
        version=version,
    )
