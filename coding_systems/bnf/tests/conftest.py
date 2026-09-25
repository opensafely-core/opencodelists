from unittest.mock import patch

import pytest


@pytest.fixture
def mocked_odp_response_data():
    return {
        "result": {
            "resources": [
                {
                    "name": "BNF_CODE_CURRENT_202503_VERSION_88",
                    "url": "https://example.com/download/bnf_code_current_202503_version_88.csv",
                },
                {
                    "name": "BNF_CODE_CURRENT_202607_VERSION_90_FINAL",
                    "url": "https://example.com/download/bnf_code_current_202607_version_90.csv",
                },
                {
                    "name": "BNF_CODE_CURRENT_202608_VERSION_90",
                    "url": "https://example.com/download/bnf_code_current_202608_version_90.csv",
                },
            ]
        }
    }


@pytest.fixture
def mocked_get(mocked_odp_response_data):
    with patch("coding_systems.bnf.fetch_data.requests.get") as mocked_get:
        mocked_get.return_value.json.return_value = mocked_odp_response_data
        yield mocked_get


@pytest.fixture
def mock_bnf_data_dir(tmp_path):
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
def mock_empty_bnf_data_dir(tmp_path):
    """Fixture to create a temporary directory with a 'bnf' subdirectory containing no files.

    Returns the temporary directory Path object.
    """
    csv_dir = tmp_path / "bnf"
    csv_dir.mkdir()

    return tmp_path
