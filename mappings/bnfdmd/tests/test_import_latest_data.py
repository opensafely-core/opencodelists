import datetime
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command


@patch("mappings.bnfdmd.import_data.import_release", autospec=True)
def test_calls_import_release_function(mock_import_release, tmpdir, mock_data_download):
    call_command(
        "import_latest_data",
        "mappings.bnfdmd",
        tmpdir,
    )
    mock_import_release.assert_called_once()
    mock_import_release.assert_called_with(
        Path(tmpdir) / "BNF Snomed Mapping data 20240101.zip",
        "20240101",
        datetime.datetime(2024, 1, 1, 0, 0),
    )
