import re
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from coding_systems.conftest import mock_migrate_coding_system
from coding_systems.dmd.import_data import import_data
from coding_systems.dmd.models import AMP, AMPP, VMP, VMPP, VPI
from coding_systems.versioning.models import CodingSystemRelease
from mappings.dmdvmpprevmap.models import Mapping as VmpPrevMapping

MOCK_DMD_IMPORT_DATA_PATH = (
    Path(__file__).parents[1] / "fixtures" / "import_resources" / "dmd_data.zip"
)


@pytest.fixture(autouse=True)
def mock_migrate():
    with patch(
        "coding_systems.base.import_data_utils.call_command", mock_migrate_coding_system
    ):
        yield


@pytest.fixture(autouse=True)
def coding_systems_database_tmp_dir(coding_systems_tmp_path):
    yield coding_systems_tmp_path


def test_import_data(settings, dmd_data):

    cs_release_count = CodingSystemRelease.objects.count()

    # import mock XML data
    # This consists of the AMP 222311000001102 (Ventolin 100micrograms/dose Evohaler)
    # and its related objects, including:
    # VMP 39113611000001102 (Salbutamol 100micrograms/dose inhaler CFC free)
    #  - this VMP has a VMPPREV id 320139002
    # VPI (with FK to VMP)
    # AMPP 1479411000001101
    # VMPP 1056811000001104
    expected_ids = {
        AMP: "222311000001102",
        VMP: "39113611000001102",
        AMPP: "1479411000001101",
        VMPP: "1056811000001104",
    }

    assert not VmpPrevMapping.objects.exists()

    import_data(
        str(MOCK_DMD_IMPORT_DATA_PATH),
        release_name="release 1 A",
        valid_from=date(2022, 10, 1),
        import_ref="Ref",
    )

    # A new CodingSystemRelease has been created
    assert CodingSystemRelease.objects.count() == cs_release_count + 1
    cs_release = CodingSystemRelease.objects.latest("id")
    assert cs_release.coding_system == "dmd"
    assert cs_release.release_name == "release 1 A"
    assert cs_release.valid_from == date(2022, 10, 1)
    assert cs_release.import_ref == "Ref"

    assert cs_release.database_alias in settings.DATABASES
    for model, expected_id in expected_ids.items():
        assert model.objects.using("dmd_release-1-a_20221001").count() == 1
        assert model.objects.using("dmd_release-1-a_20221001").first().pk == expected_id
    # VPI has been imported with a FK to the VMP
    assert VPI.objects.using("dmd_release-1-a_20221001").count() == 1
    assert (
        VPI.objects.using("dmd_release-1-a_20221001").first().vmp
        == VMP.objects.using("dmd_release-1-a_20221001").first()
    )

    # One new Mapping obj has been created, to record the previous ID for VMP
    # 39113611000001102
    assert VmpPrevMapping.objects.count() == 1
    mapping = VmpPrevMapping.objects.first()
    assert mapping.id == "39113611000001102"
    assert mapping.vpidprev == "320139002"


def test_import_data_unexpected_file():
    cs_release_count = CodingSystemRelease.objects.count()
    # import from a zip file that contains duplicate matches:
    # f_lookup2_test.xml and f_lookup2_test1.xml
    with pytest.raises(
        AssertionError,
        match=re.escape("Expected 1 path for f_lookup2_*.xml, found 2"),
    ):
        import_data(
            str(MOCK_DMD_IMPORT_DATA_PATH.parent / "dmd_data_with_extra_file.zip"),
            release_name="v2",
            valid_from=date(2022, 10, 1),
        )
    assert CodingSystemRelease.objects.count() == cs_release_count


def test_import_error(coding_systems_database_tmp_dir):
    cs_release_count = CodingSystemRelease.objects.count()

    # raise an exception after the migrate command; i.e after the setup that
    # creates the CodingSystemRelease and the new db file
    cs_release_count = CodingSystemRelease.objects.count()
    with patch(
        "coding_systems.dmd.import_data.import_model",
        side_effect=Exception("expected exception"),
    ):
        with pytest.raises(Exception, match="expected exception"):
            import_data(
                str(MOCK_DMD_IMPORT_DATA_PATH),
                release_name="v3",
                valid_from=date(2022, 10, 1),
            )

    # new CodingSystemRelease has been removed
    assert CodingSystemRelease.objects.count() == cs_release_count
    # new db path has been removed
    assert not (
        coding_systems_database_tmp_dir / "dmd" / "dmd_v3_20221001.sqlite3"
    ).exists()


def test_import_data_no_vmp_previous_mapping(dmd_data):
    # import mock XML data
    # This is the same data as dmd_data.zip (see `test_import_data` above), except that
    # VMP 39113611000001102 has no VMPPREV id
    assert not VmpPrevMapping.objects.exists()
    import_data(
        str(MOCK_DMD_IMPORT_DATA_PATH.parent / "dmd_data_no_prev_vmp.zip"),
        release_name="v4",
        valid_from=date(2022, 10, 1),
    )
    vmp = VMP.objects.using("dmd_v4_20221001").get(id="39113611000001102")
    assert vmp.vpidprev is None
    assert not VmpPrevMapping.objects.exists()
