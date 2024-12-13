from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.management import call_command

from coding_systems.versioning.models import CodingSystemRelease, ReleaseState


@patch("coding_systems.dmd.import_data.import_release")
def test_calls_import_release_function_with_extracted_release_metadata(
    mock_import_release, tmpdir, mock_data_download
):
    call_command(
        "import_latest_data",
        "dmd",
        tmpdir,
    )
    mock_import_release.assert_called_once()
    mock_import_release.assert_called_with(
        Path(tmpdir) / "nhsbsa_dmd_1.0.0_20221001000001.zip",
        "2022 1.0.0",
        date(2022, 10, 1),
    )


def test_calls_import_release_function_coding_system_release_already_exists(
    tmpdir, capsys, mock_data_download
):
    CodingSystemRelease.objects.create(
        coding_system="dmd",
        release_name="2022 1.0.0",
        valid_from=date(2022, 10, 1),
        state=ReleaseState.READY,
    )
    with pytest.raises(SystemExit) as error:
        call_command(
            "import_latest_data",
            "dmd",
            tmpdir,
        )
    assert error.value.code == 1
    captured = capsys.readouterr()
    assert (
        "A coding_systems.dmd coding system release already exists for the latest release (1.0.0) "
        "and valid from date (2022-10-01)." in captured.out
    )
