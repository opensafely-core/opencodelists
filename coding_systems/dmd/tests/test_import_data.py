import re
from datetime import date
from unittest.mock import patch

import pytest
from django.conf import settings

from coding_systems.base.tests.dynamic_db_classes import (
    DynamicDatabaseTestCase,
    DynamicDatabaseTestCaseWithTmpPath,
)
from coding_systems.dmd.data_downloader import Downloader
from coding_systems.dmd.import_data import import_data
from coding_systems.dmd.models import AMP, AMPP, VMP, VMPP, VPI
from coding_systems.versioning.models import CodingSystemRelease
from mappings.dmdvmpprevmap.models import Mapping as VmpPrevMapping

from .conftest import MOCK_DMD_IMPORT_DATA_PATH


class TestImportData(DynamicDatabaseTestCase):
    db_alias = "dmd_2022-100_20221001"
    import_data_path = MOCK_DMD_IMPORT_DATA_PATH

    @pytest.fixture
    def _get_dmd_version_asthma_medication(self, dmd_version_asthma_medication):
        self.dmd_version_asthma_medication = dmd_version_asthma_medication

    @pytest.mark.usefixtures(
        "mock_data_download", "dmd_data", "_get_dmd_version_asthma_medication"
    )
    def test_import_data(self):
        cs_release_count = CodingSystemRelease.objects.count()
        assert self.dmd_version_asthma_medication.cached_csv_data == {}

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
            self.import_data_path,
            release_name="2022 1.0.0",
            valid_from=date(2022, 10, 1),
        )

        # A new CodingSystemRelease has been created
        assert CodingSystemRelease.objects.count() == cs_release_count + 1
        cs_release = CodingSystemRelease.objects.latest("id")
        assert cs_release.coding_system == "dmd"
        assert cs_release.release_name == "2022 1.0.0"
        assert cs_release.valid_from == date(2022, 10, 1)
        # no import ref, defaults to zipfile name
        assert cs_release.import_ref == "nhsbsa_dmd_1.0.0_20221001000001.zip"

        assert cs_release.database_alias in settings.DATABASES

        for model, expected_id in expected_ids.items():
            assert model.objects.using("dmd_2022-100_20221001").count() == 1
            assert (
                model.objects.using("dmd_2022-100_20221001").first().pk == expected_id
            )
        # VPI has been imported with a FK to the VMP
        assert VPI.objects.using("dmd_2022-100_20221001").count() == 1
        assert (
            VPI.objects.using("dmd_2022-100_20221001").first().vmp
            == VMP.objects.using("dmd_2022-100_20221001").first()
        )

        # One new Mapping obj has been created, to record the previous ID for VMP
        # 39113611000001102
        assert VmpPrevMapping.objects.count() == 1
        mapping = VmpPrevMapping.objects.first()
        assert mapping.id == "39113611000001102"
        assert mapping.vpidprev == "320139002"

        # download data on existing CodelistVersions has been cached
        self.dmd_version_asthma_medication.refresh_from_db()
        assert (
            self.dmd_version_asthma_medication.cached_csv_data["release"]
            == "dmd_2022-100_20221001"
        )


class TestImportDataUnexpectedFile(DynamicDatabaseTestCase):
    db_alias = "dmd_2022-110_20221001"
    import_data_path = MOCK_DMD_IMPORT_DATA_PATH

    @pytest.mark.usefixtures("mock_data_download_bad_zip")
    def test_import_data_unexpected_file(self):
        cs_release_count = CodingSystemRelease.objects.count()
        # import from a zip file that contains duplicate matches:
        # f_lookup2_test.xml and f_lookup2_test1.xml
        with pytest.raises(
            AssertionError,
            match=re.escape("Expected 1 path for f_lookup2_*.xml, found 2"),
        ):
            import_data(
                self.import_data_path,
                release_name="2022 1.1.0",
                valid_from=date(2022, 10, 1),
            )
        assert CodingSystemRelease.objects.count() == cs_release_count


class TestImportError(DynamicDatabaseTestCaseWithTmpPath):
    db_alias = "dmd_2022-101_20220901"
    import_data_path = MOCK_DMD_IMPORT_DATA_PATH
    coding_system_subpath_name = "dmd"

    @pytest.mark.usefixtures("mock_data_download_error")
    def test_import_error(self):
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
                    self.import_data_path,
                    release_name="2022 1.0.1",
                    valid_from=date(2022, 9, 1),
                )

        # new CodingSystemRelease has been removed
        assert CodingSystemRelease.objects.count() == cs_release_count
        # new db path has been removed
        assert not (
            self.coding_systems_tmp_path / "dmd" / "dmd_2022-100_20220901.sqlite3"
        ).exists()


class TestImportDataNoVMPPreviousMapping(DynamicDatabaseTestCase):
    db_alias = "dmd_2022-120_20221001"
    import_data_path = MOCK_DMD_IMPORT_DATA_PATH

    @pytest.mark.usefixtures("dmd_data", "mock_data_download_no_prev_vmp")
    def test_import_data_no_vmp_previous_mapping(self):
        # import mock XML data
        # This is the same data as dmd_data.zip (see `test_import_data` above), except that
        # VMP 39113611000001102 has no VMPPREV id
        assert not VmpPrevMapping.objects.exists()
        import_data(
            self.import_data_path,
            release_name="2022 1.2.0",
            valid_from=date(2022, 10, 1),
        )
        vmp = VMP.objects.using("dmd_2022-120_20221001").get(id="39113611000001102")
        assert vmp.vpidprev is None
        assert not VmpPrevMapping.objects.exists()


def test_import_no_matching_release(mock_data_download):
    with pytest.raises(
        ValueError,
        match="No matching release found for release unknown-release, valid from 2022-10-01",
    ):
        import_data(
            MOCK_DMD_IMPORT_DATA_PATH,
            release_name="unknown-release",
            valid_from=date(2022, 10, 1),
        )


def test_get_release_metadata():
    # fetch release metadata for a release that is not the first one
    release = {
        "id": "1",
        "archiveFileName": "nhsbsa_dmd_2.0.0_20220101000001.zip",
        "archiveFileUrl": "https://download/nhsbsa_dmd_2.0.0_20220101000001.zip",
        "releaseDate": "2022-01-01",
    }
    assert Downloader("").get_release_metadata(release) == {
        "release": "2.0.0",
        "valid_from": date(2022, 1, 1),
        "url": "https://download/nhsbsa_dmd_2.0.0_20220101000001.zip",
        "filename": "nhsbsa_dmd_2.0.0_20220101000001.zip",
        "release_name": "2022 2.0.0",
    }


def test_get_latest_release_metadata(mock_data_download):
    assert Downloader("").get_latest_release_metadata() == {
        "release": "1.0.0",
        "valid_from": date(2022, 10, 1),
        "url": "https://download/nhsbsa_dmd_1.0.0_20221001000001.zip",
        "filename": "nhsbsa_dmd_1.0.0_20221001000001.zip",
        "release_name": "2022 1.0.0",
    }
