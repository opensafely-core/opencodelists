from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command


def test_unknown_mapping_module(tmpdir):
    with pytest.raises(CommandError, match="invalid choice: 'mappings.unknown'"):
        call_command("import_mapping_data", "mappings.unknown", tmpdir)


@patch("mappings.bnfdmd.import_data.import_data")
def test_calls_import_data_function_non_coding_system_import(mock_import_data, tmpdir):
    # A non-coding system import doesn't require the extra args
    call_command("import_mapping_data", "mappings.bnfdmd", tmpdir)
    mock_import_data.assert_called_once()
    mock_import_data.assert_called_with(str(tmpdir))
