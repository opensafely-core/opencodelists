import re

import requests
from requests.exceptions import RequestException


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

    Returns a dict containing the name, date, version, and CSV download url for the latest available BNF coding system release.
    """

    bnf_latest_release_data = response.json()["result"]["resources"][-1]

    # As of March 2025, release names are formatted as follows: 'BNF_CODE_CURRENT_202608_VERSION_90'
    release_name = bnf_latest_release_data["name"]

    # BNF CSV files are named e.g. bnf_code_current_202503_version_88.csv.
    # Get the date and the version of the latest BNF release, so we can
    # check these against CSV filenames we already have later
    match = re.match(r"^BNF_CODE_CURRENT_(\d{6})_VERSION_(\d+)(_FINAL)?$", release_name)

    release_date = match.group(1)
    release_version = match.group(2)
    release_url = bnf_latest_release_data["url"]

    latest_bnf_release_info = {
        "name": release_name,
        "date": release_date,
        "version": release_version,
        "url": release_url,
    }

    return latest_bnf_release_info
