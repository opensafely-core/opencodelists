import re
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
import responses
from django.conf import settings

from coding_systems.conftest import mock_migrate_coding_system
from coding_systems.dmd.import_data import import_data
from coding_systems.dmd.models import AMP, AMPP, VMP, VMPP, VPI
from coding_systems.versioning.models import CodingSystemRelease
from mappings.dmdvmpprevmap.models import Mapping as VmpPrevMapping

MOCK_DMD_IMPORT_DATA_PATH = Path(__file__).parents[1] / "fixtures" / "import_resources"


@pytest.fixture(autouse=True)
def mock_migrate():
    with patch(
        "coding_systems.base.import_data_utils.call_command", mock_migrate_coding_system
    ):
        yield


def add_response(rsps, filename):
    rsps.add(
        responses.GET,
        f"https://isd.digital.nhs.uk/trud/api/v1/keys/{settings.TRUD_API_KEY}/items/24/releases",
        json={
            "api": "v1",
            "releases": [
                {
                    "id": "1",
                    "archiveFileName": filename,
                    "archiveFileUrl": f"https://download/{filename}",
                }
            ],
        },
        status=200,
    )


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def mock_data_download(mocked_responses):
    filename = "nhsbsa_dmd_test_20221001000001.zip"
    add_response(mocked_responses, filename)
    with patch(
        "coding_systems.dmd.import_data.get_file",
        return_value=filename,
    ):
        yield


@pytest.fixture
def mock_data_download_bad_zip(mocked_responses):
    filename = "nhsbsa_dmd_test-extra-file_20221001000001.zip"
    add_response(mocked_responses, filename)
    with patch(
        "coding_systems.dmd.import_data.get_file",
        return_value=filename,
    ):
        yield


@pytest.fixture
def mock_data_download_no_prev_vmp(mocked_responses):
    filename = "nhsbsa_dmd_test-no-prev-vmp_20221001000001.zip"
    add_response(mocked_responses, filename)
    with patch(
        "coding_systems.dmd.import_data.get_file",
        return_value=filename,
    ):
        yield


@pytest.fixture(autouse=True)
def coding_systems_database_tmp_dir(coding_systems_tmp_path):
    yield coding_systems_tmp_path


def test_import_data(settings, dmd_data, mock_data_download):
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
        release_name="2022 test",
        valid_from=date(2022, 10, 1),
    )

    # A new CodingSystemRelease has been created
    assert CodingSystemRelease.objects.count() == cs_release_count + 1
    cs_release = CodingSystemRelease.objects.latest("id")
    assert cs_release.coding_system == "dmd"
    assert cs_release.release_name == "2022 test"
    assert cs_release.valid_from == date(2022, 10, 1)
    # no import ref, defaults to zipfile name
    assert cs_release.import_ref == "nhsbsa_dmd_test_20221001000001.zip"

    assert cs_release.database_alias in settings.DATABASES
    for model, expected_id in expected_ids.items():
        assert model.objects.using("dmd_2022-test_20221001").count() == 1
        assert model.objects.using("dmd_2022-test_20221001").first().pk == expected_id
    # VPI has been imported with a FK to the VMP
    assert VPI.objects.using("dmd_2022-test_20221001").count() == 1
    assert (
        VPI.objects.using("dmd_2022-test_20221001").first().vmp
        == VMP.objects.using("dmd_2022-test_20221001").first()
    )

    # One new Mapping obj has been created, to record the previous ID for VMP
    # 39113611000001102
    assert VmpPrevMapping.objects.count() == 1
    mapping = VmpPrevMapping.objects.first()
    assert mapping.id == "39113611000001102"
    assert mapping.vpidprev == "320139002"


def test_import_data_unexpected_file(mock_data_download_bad_zip):
    cs_release_count = CodingSystemRelease.objects.count()
    # import from a zip file that contains duplicate matches:
    # f_lookup2_test.xml and f_lookup2_test1.xml
    with pytest.raises(
        AssertionError,
        match=re.escape("Expected 1 path for f_lookup2_*.xml, found 2"),
    ):
        import_data(
            str(MOCK_DMD_IMPORT_DATA_PATH),
            release_name="test-extra-file",
            valid_from=date(2022, 10, 1),
        )
    assert CodingSystemRelease.objects.count() == cs_release_count


def test_import_error(coding_systems_database_tmp_dir, mock_data_download):
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
                release_name="test",
                valid_from=date(2022, 10, 1),
            )

    # new CodingSystemRelease has been removed
    assert CodingSystemRelease.objects.count() == cs_release_count
    # new db path has been removed
    assert not (
        coding_systems_database_tmp_dir / "dmd" / "dmd_test_20221001.sqlite3"
    ).exists()


def test_import_data_no_vmp_previous_mapping(dmd_data, mock_data_download_no_prev_vmp):
    # import mock XML data
    # This is the same data as dmd_data.zip (see `test_import_data` above), except that
    # VMP 39113611000001102 has no VMPPREV id
    assert not VmpPrevMapping.objects.exists()
    import_data(
        str(MOCK_DMD_IMPORT_DATA_PATH),
        release_name="test-no-prev-vmp",
        valid_from=date(2022, 10, 1),
    )
    vmp = VMP.objects.using("dmd_test-no-prev-vmp_20221001").get(id="39113611000001102")
    assert vmp.vpidprev is None
    assert not VmpPrevMapping.objects.exists()


def test_import_no_matching_release(mock_data_download):
    with pytest.raises(
        ValueError,
        match="No matching release found for expected filename nhsbsa_dmd_unknown-release_20221001000001.zip",
    ):
        import_data(
            str(MOCK_DMD_IMPORT_DATA_PATH),
            release_name="unknown-release",
            valid_from=date(2022, 10, 1),
        )
