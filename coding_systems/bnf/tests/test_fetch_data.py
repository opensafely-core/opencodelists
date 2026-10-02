from pathlib import Path
from unittest.mock import patch

import pytest
import responses
from requests.exceptions import HTTPError, Timeout

from coding_systems.bnf.fetch_data import (
    BNFReleaseInfo,
    download_csv,
    fetch_data,
    find_latest_local_csv,
    find_latest_release,
    get_all_releases,
    have_latest_csv,
    parse_name,
)


CURRENT_RELEASE_INFO = BNFReleaseInfo(
    name="BNF_CODE_CURRENT_202608_VERSION_90",
    date="202608",
    version=90,
    url="https://example.com/download/bnf_code_current_202608_version_90.csv",
)

NEW_RELEASE_INFO = BNFReleaseInfo(
    date="202609",
    name="BNF_CODE_CURRENT_202609_VERSION_90",
    url="https://example.com/download/bnf_code_current_202609_version_90.csv",
    version=90,
)

CSV_FILE = """\
BNF_CHAPTER,BNF_CHAPTER_CODE
"Gastro-Intestinal System",01
"Cardiovascular System",02
"""


@pytest.fixture
def mocked_odp_data():
    """Fixture that returns a dict of data representing a deserialized ODP API response."""
    return {
        "result": {
            "resources": [
                {
                    "name": "BNF_CODE_CURRENT_202503_VERSION_88",
                    "url": "https://example.com/download/bnf_code_current_202503_version_88.csv",
                },
                {
                    "name": "BNF_CODE_CURRENT_202608_VERSION_90",
                    "url": "https://example.com/download/bnf_code_current_202608_version_90.csv",
                },
                {
                    "name": "BNF_CODE_CURRENT_202607_VERSION_90_FINAL",
                    "url": "https://example.com/download/bnf_code_current_202607_version_90.csv",
                },
            ]
        }
    }


@pytest.fixture
def mocked_get(mocked_odp_data):
    """Patch requests.get() in coding_systems.bnf.fetch_data.

    The mocked response's `.json()` method returns the
    `mocked_odp_data` fixture.
    """
    with patch("coding_systems.bnf.fetch_data.requests.get") as mocked_get:
        mocked_get.return_value.json.return_value = mocked_odp_data
        yield mocked_get


@pytest.fixture
def mock_base_dir(tmp_path):
    """Fixture to create a temporary directory with a 'bnf' subdirectory containing mock BNF coding release system CSVs.

    Returns the temporary directory Path object.
    """
    csv_dir = tmp_path / "bnf"
    csv_dir.mkdir()

    csv_files = [
        "bnf_code_current_202608_version_90.csv",
        "bnf_code_current_202508_version_90.csv",
        "bnf_code_current_202508_version_88.csv",
        "bnf_code_current_202502_version_88.csv",
        "bnf_code_current_202409_version_86.csv",
    ]

    for file in csv_files:
        (csv_dir / file).touch()

    return tmp_path


@pytest.fixture
def mock_empty_base_dir(tmp_path):
    """Fixture to create a temporary directory with an empty 'bnf' subdirectory.

    Returns the temporary directory Path object.
    """
    csv_dir = tmp_path / "bnf"
    csv_dir.mkdir()

    return tmp_path


def test_get_all_releases_success(mocked_get, mocked_odp_data):

    response = get_all_releases()

    mocked_get.assert_called_once_with(
        "https://opendata.nhsbsa.net/api/3/action/package_show?id=bnf-code-information-current-year",
        timeout=10,
    )
    mocked_get.return_value.raise_for_status.assert_called_once()
    assert response is mocked_odp_data


def test_get_all_releases_http_error(mocked_get):
    mocked_get.return_value.raise_for_status.side_effect = HTTPError("500 Server Error")

    with pytest.raises(HTTPError) as exc_info:
        get_all_releases()

    assert (
        "Failed to fetch the latest BNF release information from ODP"
        in exc_info.value.__notes__
    )


def test_get_all_releases_data_timeout(mocked_get):
    mocked_get.side_effect = Timeout("Request timed out")
    with pytest.raises(Timeout) as exc_info:
        get_all_releases()

    assert (
        "Failed to fetch the latest BNF release information from ODP"
        in exc_info.value.__notes__
    )


def test_find_latest_release(mocked_odp_data):

    latest_info = find_latest_release(mocked_odp_data)

    assert latest_info == CURRENT_RELEASE_INFO


@pytest.mark.parametrize(
    "name",
    [
        pytest.param(
            "BNF_CODE_CURRENT_202608_VERSION_90",
            id="name_upper",
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
        pytest.param(
            "bnf_code_202608_version_90.csv",
            id="filename_legacy",
        ),
    ],
)
def test_parse_name(name):
    date, version = parse_name(name)
    assert date == "202608"
    assert version == 90


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("not_a_bnf_file.csv", id="invalid_name"),
        pytest.param(
            "bnf_code_current_202608.csv",
            id="missing_version",
        ),
    ],
)
def test_parse_name_invalid(name):
    with pytest.raises(ValueError) as exc_info:
        parse_name(name)

    assert str(exc_info.value) == (f"Unexpected BNF release name: {name}")


def test_find_latest_local_csv_existing_files(mock_base_dir):
    csv_path = find_latest_local_csv(mock_base_dir / "bnf")

    assert csv_path.name == "bnf_code_current_202608_version_90.csv"


def test_find_latest_local_csv_no_files(mock_empty_base_dir):
    csv_path = find_latest_local_csv(mock_empty_base_dir / "bnf")

    assert csv_path is None


def test_have_latest_csv_with_latest_local_csv():

    latest_odp_release = CURRENT_RELEASE_INFO

    latest_local_csv = Path("bnf_code_current_202608_version_90.csv")

    assert have_latest_csv(latest_odp_release, latest_local_csv)


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
def test_have_latest_csv_with_outdated_local_csv(csv_path):

    latest_odp_release = CURRENT_RELEASE_INFO

    assert not have_latest_csv(latest_odp_release, csv_path)


@responses.activate
def test_download_csv_success(mock_base_dir):
    latest_odp_release = NEW_RELEASE_INFO

    responses.get(
        latest_odp_release.url,
        body=CSV_FILE.encode("utf-8"),
        status=200,
    )

    new_csv = download_csv(
        latest_odp_release,
        mock_base_dir / "bnf",
    )

    assert new_csv == (mock_base_dir / "bnf" / "bnf_code_current_202609_version_90.csv")
    assert new_csv.read_text() == CSV_FILE


@responses.activate
def test_download_csv_http_error(mock_base_dir):
    latest_odp_release = NEW_RELEASE_INFO

    responses.get(
        latest_odp_release.url,
        body=CSV_FILE.encode("utf-8"),
        status=500,
    )

    with pytest.raises(HTTPError) as exc_info:
        download_csv(
            latest_odp_release,
            mock_base_dir / "bnf",
        )

    assert (
        "Failed to download the latest BNF release CSV from ODP"
        in exc_info.value.__notes__
    )


@responses.activate
def test_download_csv_timeout_error(mock_base_dir):
    latest_odp_release = NEW_RELEASE_INFO

    responses.get(
        latest_odp_release.url,
        body=Timeout("Request timed out"),
    )

    with pytest.raises(Timeout) as exc_info:
        download_csv(
            latest_odp_release,
            mock_base_dir / "bnf",
        )

    assert (
        "Failed to download the latest BNF release CSV from ODP"
        in exc_info.value.__notes__
    )


@responses.activate
def test_fetch_data_existing_csv_new_release_available(mock_base_dir):

    latest_odp_release = NEW_RELEASE_INFO

    responses.get(
        "https://opendata.nhsbsa.net/api/3/action/package_show?id=bnf-code-information-current-year",
        json={
            "result": {
                "resources": [
                    {
                        "name": "BNF_CODE_CURRENT_202608_VERSION_90",
                        "url": "https://example.com/download/bnf_code_current_202608_version_90.csv",
                    },
                    {
                        "name": "BNF_CODE_CURRENT_202609_VERSION_90",
                        "url": "https://example.com/download/bnf_code_current_202609_version_90.csv",
                    },
                ]
            }
        },
        status=200,
    )

    responses.get(
        latest_odp_release.url,
        body=CSV_FILE.encode("utf-8"),
        status=200,
    )

    new_csv = fetch_data(mock_base_dir)

    assert new_csv == (mock_base_dir / "bnf" / "bnf_code_current_202609_version_90.csv")
    assert new_csv.read_text() == CSV_FILE


@responses.activate
def test_fetch_data_no_existing_csv(mock_empty_base_dir):

    latest_odp_release = NEW_RELEASE_INFO

    responses.get(
        "https://opendata.nhsbsa.net/api/3/action/package_show?id=bnf-code-information-current-year",
        json={
            "result": {
                "resources": [
                    {
                        "name": "BNF_CODE_CURRENT_202608_VERSION_90",
                        "url": "https://example.com/download/bnf_code_current_202608_version_90.csv",
                    },
                    {
                        "name": "BNF_CODE_CURRENT_202609_VERSION_90",
                        "url": "https://example.com/download/bnf_code_current_202609_version_90.csv",
                    },
                ]
            }
        },
        status=200,
    )

    responses.get(
        latest_odp_release.url,
        body=CSV_FILE.encode("utf-8"),
        status=200,
    )

    new_csv = fetch_data(mock_empty_base_dir)

    assert new_csv == (
        mock_empty_base_dir / "bnf" / "bnf_code_current_202609_version_90.csv"
    )
    assert new_csv.read_text() == CSV_FILE


@responses.activate
def test_fetch_data_existing_csv_no_new_release_available(
    mock_base_dir, mocked_odp_data
):

    responses.get(
        "https://opendata.nhsbsa.net/api/3/action/package_show?id=bnf-code-information-current-year",
        json=mocked_odp_data,
        status=200,
    )

    new_csv = fetch_data(mock_base_dir)

    assert new_csv is None
    assert len(responses.calls) == 1
