from datetime import date

import pytest
import responses

from coding_systems.bnf.data_downloader import Downloader


NEW_RELEASE_INFO = {
    "date": "202609",
    "name": "BNF_CODE_CURRENT_202609_VERSION_90",
    "url": "https://example.com/download/bnf_code_current_202609_version_90.csv",
    "version": 90,
}

CSV_FILE = """\
BNF_CHAPTER,BNF_CHAPTER_CODE
"Gastro-Intestinal System",01
"Cardiovascular System",02
"""

ODP_URL = "https://opendata.nhsbsa.net/api/3/action/package_show?id=bnf-code-information-current-year"


@pytest.fixture
def mock_bnf_data_dir(tmp_path):
    """Fixture to create a temporary directory with a 'bnf' subdirectory containing mock BNF coding release system CSVs.

    Returns the BNF subdirectory Path object.
    """
    csv_dir = tmp_path / "bnf"
    csv_dir.mkdir()

    csv_files = [
        "bnf_code_current_202608_version_90.csv",
        "bnf_code_current_202607_version_90.csv",
    ]

    for file in csv_files:
        (csv_dir / file).touch()

    return csv_dir


@responses.activate
def test_download_latest_release_success(mock_bnf_data_dir):
    """Test that we download the latest BNF CSV and return its path and release metadata."""

    responses.get(
        ODP_URL,
        json={
            "result": {
                "resources": [
                    {
                        "name": "BNF_CODE_CURRENT_202608_VERSION_90",
                        "url": "https://example.com/download/bnf_code_current_202608_version_90.csv",
                    },
                    {
                        "name": NEW_RELEASE_INFO["name"],
                        "url": NEW_RELEASE_INFO["url"],
                    },
                    {
                        "name": "BNF_CODE_CURRENT_202607_VERSION_90",
                        "url": "https://example.com/download/bnf_code_current_202607_version_90.csv",
                    },
                ]
            }
        },
        status=200,
    )

    responses.get(
        NEW_RELEASE_INFO["url"],
        body=CSV_FILE.encode("utf-8"),
        status=200,
    )

    downloader = Downloader(mock_bnf_data_dir)
    release_csv_path, metadata = downloader.download_latest_release()

    assert (
        release_csv_path == mock_bnf_data_dir / "bnf_code_current_202609_version_90.csv"
    )
    assert metadata == {
        "release": "90 (2026-09-01)",
        "release_name": "90 (2026-09-01)",
        "valid_from": date(2026, 9, 1),
        "import_ref": "bnf_code_current_202609_version_90.csv",
    }
    assert release_csv_path.read_text() == CSV_FILE


@responses.activate
def test_download_latest_release_handles_latest_csv_already_downloaded(
    mock_bnf_data_dir,
):
    """Test that we do not download the latest BNF CSV when we already have it locally."""

    responses.get(
        ODP_URL,
        json={
            "result": {
                "resources": [
                    {
                        "name": "BNF_CODE_CURRENT_202608_VERSION_90",
                        "url": "https://example.com/download/bnf_code_current_202608_version_90.csv",
                    },
                    {
                        "name": NEW_RELEASE_INFO["name"],
                        "url": NEW_RELEASE_INFO["url"],
                    },
                    {
                        "name": "BNF_CODE_CURRENT_202607_VERSION_90",
                        "url": "https://example.com/download/bnf_code_current_202607_version_90.csv",
                    },
                ]
            }
        },
        status=200,
    )

    responses.get(
        NEW_RELEASE_INFO["url"],
        body=CSV_FILE.encode("utf-8"),
        status=200,
    )

    (mock_bnf_data_dir / "bnf_code_current_202609_version_90.csv").touch()

    downloader = Downloader(mock_bnf_data_dir)
    release_csv_path, metadata = downloader.download_latest_release()

    assert (
        release_csv_path == mock_bnf_data_dir / "bnf_code_current_202609_version_90.csv"
    )
    assert metadata == {
        "release": "90 (2026-09-01)",
        "release_name": "90 (2026-09-01)",
        "valid_from": date(2026, 9, 1),
        "import_ref": "bnf_code_current_202609_version_90.csv",
    }

    assert len(responses.calls) == 1
