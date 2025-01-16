from datetime import date
from unittest.mock import patch

import pytest
from django.conf import settings

from coding_systems.base.tests.dynamic_db_classes import DynamicDatabaseTestCase
from coding_systems.conftest import mock_migrate_coding_system
from coding_systems.snomedct.import_data import import_data
from coding_systems.snomedct.models import Concept
from coding_systems.versioning.models import CodingSystemRelease

from .conftest import MOCK_SNOMEDCT_IMPORT_DATA_PATH


class TestImportData(DynamicDatabaseTestCase):
    db_alias = "snomedct_200_20230101"
    import_data_path = str(MOCK_SNOMEDCT_IMPORT_DATA_PATH)

    @pytest.mark.usefixtures("mock_data_download")
    def test_import_data(self):
        cs_release_count = CodingSystemRelease.objects.count()

        # import mock data
        # This consists of a very small subset of 6 Snomed concepts
        #
        # 3723001        Arthritis
        # 439656005        └ Arthritis of elbow
        # 202855006           └ Lateral epicondylitis
        # 312411000119100        ├ Lateral epicondylitis of left humerus
        # 15636001000119108      |  └ Lateral epicondylitis of bilateral humerus
        # 312421000119107        └ Lateral epicondylitis of left humerus
        # 15636001000119108         └ Lateral epicondylitis of bilateral humerus

        with patch(
            "coding_systems.base.import_data_utils.call_command",
            mock_migrate_coding_system,
        ):
            import_data(
                self.import_data_path,
                release_name="2.0.0",
                valid_from=date(2023, 1, 1),
            )

        # A new CodingSystemRelease has been created
        assert CodingSystemRelease.objects.count() == cs_release_count + 1
        cs_release = CodingSystemRelease.objects.latest("id")
        assert cs_release.coding_system == "snomedct"
        assert cs_release.release_name == "2.0.0"
        assert cs_release.valid_from == date(2023, 1, 1)
        assert cs_release.import_ref == "uk_sct2cl_2.0.0_20230101000001Z.zip"

        assert cs_release.database_alias in settings.DATABASES
        concepts = Concept.objects.using(cs_release.database_alias).all()
        assert concepts.count() == 6
        assert set(concepts.values_list("id", flat=True)) == {
            "3723001",
            "439656005",
            "202855006",
            "312411000119100",
            "312421000119107",
            "15636001000119108",
        }
