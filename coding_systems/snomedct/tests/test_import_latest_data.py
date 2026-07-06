from datetime import date
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command


@patch("coding_systems.snomedct.import_data.import_release", autospec=True)
def test_calls_import_release_function_with_extracted_release_metadata(
    mock_import_release, tmpdir, mock_data_download
):
    call_command(
        "import_latest_data",
        "snomedct",
        tmpdir,
    )
    mock_import_release.assert_called_once()
    mock_import_release.assert_called_with(
        Path(tmpdir) / "uk_sct2cl_2.0.0_20230101000001Z.zip",
        release="2.0.0",
        valid_from=date(2023, 1, 1),
        url="https://download/uk_sct2cl_2.0.0_20230101000001Z.zip",
        filename="uk_sct2cl_2.0.0_20230101000001Z.zip",
        release_name="2.0.0",
    )
