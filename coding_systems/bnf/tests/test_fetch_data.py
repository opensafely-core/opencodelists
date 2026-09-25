from pathlib import Path

import pytest
import responses
from requests.exceptions import HTTPError, Timeout

from coding_systems.bnf.fetch_data import (
    BNFReleaseInfo,
    download_latest_bnf_release,
    get_bnf_release_date_and_version,
    get_current_year_bnf_releases_info,
    get_latest_bnf_release_csv_info,
    get_latest_bnf_release_info,
    release_csv_outdated,
)


def test_get_current_year_bnf_releases_info_success(mocked_get):

    response = get_current_year_bnf_releases_info()

    mocked_get.assert_called_once_with(
        "https://opendata.nhsbsa.net/api/3/action/package_show?id=bnf-code-information-current-year",
        timeout=10,
    )
    response.raise_for_status.assert_called_once()
    assert response is mocked_get.return_value


def test_get_current_year_bnf_releases_info_http_error(mocked_get):
    mocked_get.return_value.raise_for_status.side_effect = HTTPError("500 Server Error")

    with pytest.raises(HTTPError) as exc_info:
        get_current_year_bnf_releases_info()

    assert (
        "Failed to fetch the latest BNF release information from ODP"
        in exc_info.value.__notes__
    )


def test_get_current_year_bnf_releases_info_timeout(mocked_get):
    mocked_get.side_effect = Timeout("Request timed out")
    with pytest.raises(Timeout) as exc_info:
        get_current_year_bnf_releases_info()

    assert (
        "Failed to fetch the latest BNF release information from ODP"
        in exc_info.value.__notes__
    )


def test_get_latest_bnf_release_info(mocked_odp_response):

    latest_bnf_release_info = get_latest_bnf_release_info(mocked_odp_response)

    assert latest_bnf_release_info == BNFReleaseInfo(
        name="BNF_CODE_CURRENT_202608_VERSION_90",
        date="202608",
        version=90,
        url="https://example.com/download/bnf_code_current_202608_version_90.csv",
    )


@pytest.mark.parametrize(
    "bnf_release_name",
    [
        pytest.param(
            "BNF_CODE_CURRENT_202608_VERSION_90",
            id="name_uppercase",
        ),
        pytest.param(
            "bnf_code_current_202608_version_90",
            id="name_lower",
        ),
        pytest.param(
            "BNF_CODE_CURRENT_202608_VERSION_90_FINAL",
            id="name_upper_final",
        ),
        pytest.param(
            "bnf_code_current_202608_version_90.csv",
            id="filename_lower",
        ),
        pytest.param(
            "BNF_CODE_CURRENT_202608_VERSION_90.csv",
            id="filename_upper",
        ),
        pytest.param(
            "bnf_code_current_202608_version_90_final.csv",
            id="filename_lower_final",
        ),
    ],
)
def test_get_bnf_release_date_and_version(bnf_release_name):
    date, version = get_bnf_release_date_and_version(bnf_release_name)
    assert date == "202608"
    assert version == 90


def test_get_latest_bnf_release_csv_info_existing_files(mock_bnf_data_dir):
    latest_csv_path = get_latest_bnf_release_csv_info(mock_bnf_data_dir)

    assert latest_csv_path.name == "bnf_code_current_202608_version_90.csv"


def test_get_latest_bnf_release_csv_info_no_files(mock_empty_bnf_data_dir):
    latest_csv_path = get_latest_bnf_release_csv_info(mock_empty_bnf_data_dir)

    assert latest_csv_path is None


def test_release_csv_outdated_with_current_csv():

    latest_bnf_release_info = BNFReleaseInfo(
        date="202608",
        name="BNF_CODE_CURRENT_202608_VERSION_90",
        url="https://opendata.nhsbsa.net/dataset/29d25de3-02cd-4755-9dee-cdc37e37b5f3/resource/5d9f75a8-415c-45d6-a671-ec64db437468/download/bnf_code_current_202608_version_90.csv",
        version=90,
    )

    latest_bnf_release_csv_path = Path("bnf_code_current_202608_version_90.csv")

    assert not release_csv_outdated(
        latest_bnf_release_info, latest_bnf_release_csv_path
    )


@pytest.mark.parametrize(
    "csv_path",
    [
        pytest.param(
            Path("bnf_code_current_202607_version_90.csv"),
            id="older_date",
        ),
        pytest.param(
            Path("bnf_code_current_202608_version_88.csv"),
            id="older_version",
        ),
    ],
)
def test_release_csv_outdated_with_outdated_csv(csv_path):

    latest_bnf_release_info = BNFReleaseInfo(
        date="202608",
        name="BNF_CODE_CURRENT_202608_VERSION_90",
        url="https://opendata.nhsbsa.net/dataset/29d25de3-02cd-4755-9dee-cdc37e37b5f3/resource/5d9f75a8-415c-45d6-a671-ec64db437468/download/bnf_code_current_202608_version_90.csv",
        version=90,
    )

    assert release_csv_outdated(latest_bnf_release_info, csv_path)


@responses.activate
def test_download_latest_bnf_release_success(mock_bnf_data_dir):
    latest_bnf_release_info = BNFReleaseInfo(
        date="202609",
        name="BNF_CODE_CURRENT_202609_VERSION_90",
        url="https://example.com/download/bnf_code_current_202609_version_90.csv",
        version=90,
    )

    csv_file = """\
        BNF_CHAPTER,BNF_CHAPTER_CODE
        "Gastro-Intestinal System",01
        "Cardiovascular System",02
    """

    responses.get(
        latest_bnf_release_info.url,
        body=csv_file.encode("utf-8"),
        status=200,
    )

    downloaded_path = download_latest_bnf_release(
        latest_bnf_release_info,
        mock_bnf_data_dir,
    )

    assert downloaded_path == (
        mock_bnf_data_dir / "bnf_code_current_202609_version_90.csv"
    )
    assert downloaded_path.read_text() == csv_file
