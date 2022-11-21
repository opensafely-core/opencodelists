import subprocess
from datetime import date
from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command

from coding_systems.versioning.models import CodingSystemRelease, ReleaseState


def test_unknown_coding_system(tmpdir):
    with pytest.raises(CommandError, match="invalid choice: 'unknown_coding_system'"):
        call_command("import_coding_system_data", "unknown_coding_system", tmpdir)


@patch("coding_systems.bnf.import_data.import_data")
def test_calls_import_data_function_coding_system_import(mock_import_data, tmpdir):
    call_command(
        "import_coding_system_data",
        "bnf",
        tmpdir,
        release_name="version 1 A",
        valid_from=date(2022, 10, 1),
    )
    mock_import_data.assert_called_once()
    mock_import_data.assert_called_with(
        str(tmpdir),
        release_name="version 1 A",
        valid_from=date(2022, 10, 1),
        import_ref=None,
    )


def test_calls_import_data_function_coding_system_release_already_exists(
    tmpdir, capsys
):
    CodingSystemRelease.objects.create(
        coding_system="dmd",
        release_name="v1",
        valid_from=date(2022, 10, 1),
        state=ReleaseState.READY,
    )
    with pytest.raises(SystemExit) as error:
        call_command(
            "import_coding_system_data",
            "dmd",
            tmpdir,
            release_name="v1",
            valid_from=date(2022, 10, 1),
        )
    assert error.value.code == 1
    captured = capsys.readouterr()
    assert (
        "A coding system release already exists for dmd with release 'v1' and valid from date 20221001"
        in captured.out
    )


@patch("coding_systems.snomedct.import_data.import_data")
def test_calls_import_data_function_coding_system_force_overwrite(
    mock_import_data, tmpdir
):
    CodingSystemRelease.objects.create(
        coding_system="snomedct",
        release_name="v1",
        valid_from=date(2022, 10, 1),
        import_ref="A first ref",
        state=ReleaseState.READY,
    )

    call_command(
        "import_coding_system_data",
        "snomedct",
        tmpdir,
        release_name="v1",
        valid_from=date(2022, 10, 1),
        import_ref="A new ref",
        force=True,
    )

    mock_import_data.assert_called_once()
    mock_import_data.assert_called_with(
        str(tmpdir),
        release_name="v1",
        valid_from=date(2022, 10, 1),
        import_ref="A new ref",
    )


@pytest.mark.parametrize(
    "input_date,returncode,error",
    [
        ("2020-1", 2, "Not a valid date (YYYY-MM-DD): 2020-1"),
        ("20201101", 2, "Not a valid date (YYYY-MM-DD): 20201101"),
        ("Nov", 2, "Not a valid date (YYYY-MM-DD): Nov"),
        (("20200231", 2, "Not a valid date (YYYY-MM-DD): 20200231")),
    ],
)
def test_valid_from_validation(capfd, input_date, returncode, error):
    ret = subprocess.run(
        [
            "python",
            "manage.py",
            "import_coding_system_data",
            "snomedct",
            "/tmp",
            "--release",
            "v1",
            "--valid-from",
            input_date,
        ],
        check=False,
    )
    assert ret.returncode == returncode
    cap = capfd.readouterr()
    assert error in cap.err
    assert cap.out == ""
