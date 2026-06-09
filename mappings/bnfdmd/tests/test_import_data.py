from unittest.mock import patch
from zipfile import ZipFile

import pytest

from mappings.bnfdmd.import_data import import_release
from mappings.bnfdmd.models import Mapping

from .conftest import MOCK_BNFDMD_IMPORT_DATA_PATH


def test_import_release():
    """
    import mock data
    This consists of a minimal mapping file covering
    AMP/AMPP/VMP/VMPPs both with and without BNF mapping entries:

    |VMP / VMPP/ AMP / AMPP|BNF Code        |BNF Name                |SNOMED Code       |
    |----------------------|----------------|------------------------|------------------|
    |VMP                   | 0206020T0AAAGAG| Verapamil 160mg tablets| 42217211000001101|
    |VMPP                  | 0206020T0AAAGAG| Verapamil 160mg tablets| 982511000001103  |
    |AMP                   | 0212000Y0BBAAAA| Zocor 10mg tablets     | 108111000001106  |
    |AMPP                  | 0212000Y0BBAAAA| Zocor 10mg tablets     | 1328211000001104 |
    |AMP                   |                |                        | 5409611000001107 |
    |AMPP                  |                |                        | 5409811000001106 |
    |VMP                   |                |                        | 3377411000001106 |
    |VMPP                  |                |                        | 1139011000001107 |

    """

    import_release(MOCK_BNFDMD_IMPORT_DATA_PATH, None, None)

    assert Mapping.objects.count() == 4
    for dmd_type, bnf, dmd in [
        ("AMP", "0212000Y0BBAAAA", "108111000001106"),
        ("AMPP", "0212000Y0BBAAAA", "1328211000001104"),
        ("VMP", "0206020T0AAAGAG", "42217211000001101"),
        ("VMPP", "0206020T0AAAGAG", "982511000001103"),
    ]:
        mapping = Mapping.objects.get(dmd_type=dmd_type)
        assert mapping.dmd_code == dmd
        assert mapping.bnf_concept_id == bnf


@pytest.mark.parametrize(
    "workbook_zip_archive_path",
    [
        pytest.param(
            "BNF Snomed Mapping data 20260519.xlsx",
            id="root-xlsx-matching-zip-name",
        ),
        pytest.param(
            "BNF+Snomed+Mapping+data+20260319.xlsx",
            id="root-xlsx-not-matching-zip-name",
        ),
        pytest.param(
            "BNF Snomed Mapping data 20260519/BNF Snomed Mapping data 20260519.xlsx",
            id="nested-xlsx-matching-zip-name",
        ),
        pytest.param(
            "BNF Snomed Mapping data 20260519/BNF+Snomed+Mapping+data+20260319.xlsx",
            id="nested-xlsx-not-matching-zip-name",
        ),
    ],
)
def test_import_release_passes_correct_xlsx_path_to_import_data(
    tmp_path, workbook_zip_archive_path
):
    """
    Test that import_release() passes the correct xlsx workbook path to import_data().
    """
    zip_path = tmp_path / "BNF Snomed Mapping data 20260519.zip"

    # The NHSBSA BNF SNOMED mapping release is a ZIP file containing one XLSX workbook.
    with ZipFile(zip_path, "w") as zip_file:
        zip_file.writestr(
            workbook_zip_archive_path,
            "dummy_workbook_data",
        )

    with patch("mappings.bnfdmd.import_data.import_data") as mock_import_data:
        import_release(zip_path, None, None)

    mock_import_data.assert_called_once()

    workbook_path = mock_import_data.call_args.args[0]

    assert workbook_path.endswith(workbook_zip_archive_path)


@pytest.mark.parametrize(
    "zip_archive_files",
    [
        pytest.param({}, id="no-files"),
        pytest.param(
            {"README.txt": "non-workbook contents"},
            id="no-xlsx-files",
        ),
        pytest.param(
            {
                "workbook file_1.xlsx": "workbook 1 contents",
                "workbook file_2.xlsx": "workbook 2 contents",
            },
            id="two-xlsx-files",
        ),
    ],
)
def test_import_release_error_if_xlsx_count_not_one(tmp_path, zip_archive_files):
    """
    Test that import_release() raises an error if the extracted archive does not
    contain exactly one .xlsx file.
    """
    zip_path = tmp_path / "BNF Snomed Mapping data 20260519.zip"

    with ZipFile(zip_path, "w") as zip_file:
        for path_to_file, contents in zip_archive_files.items():
            zip_file.writestr(path_to_file, contents)

    with pytest.raises(ValueError, match="Expected exactly one .xlsx file"):
        import_release(zip_path, None, None)
