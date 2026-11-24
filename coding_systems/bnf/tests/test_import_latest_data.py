from datetime import date
from unittest.mock import patch

import pytest
from django.core.management import call_command


@pytest.fixture
def mock_bnf_data_dir(tmp_path):
    """Fixture to create a temporary directory with a 'bnf' subdirectory containing mock BNF coding release system CSVs.

    Returns the BNF subdirectory Path object.
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

    return csv_dir


@patch("coding_systems.bnf.import_data.import_release", autospec=True)
@patch("coding_systems.bnf.data_downloader.Downloader.download_latest_release")
def test_import_latest_data_passes_release_csv_to_importer(
    mock_download_latest_release, mock_import_release, mock_bnf_data_dir
):
    """Test that the `import_latest_data` management command passes the correct coding system release CSV path and metadata from the BNF downloader to the BNF importer."""

    release_csv_path = mock_bnf_data_dir / "bnf_code_current_202608_version_90.csv"

    metadata = {
        "release": "90 (2026-08-01)",
        "release_name": "90 (2026-08-01)",
        "valid_from": date(2026, 8, 1),
        "import_ref": "bnf_code_current_202608_version_90.csv",
    }

    mock_download_latest_release.return_value = (
        release_csv_path,
        metadata,
    )

    call_command(
        "import_latest_data",
        "bnf",
        mock_bnf_data_dir,
    )

    mock_download_latest_release.assert_called_once()

    mock_import_release.assert_called_once_with(release_csv_path, **metadata)
