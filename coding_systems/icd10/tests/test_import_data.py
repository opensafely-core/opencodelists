from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from django.conf import settings

from coding_systems.base.tests.dynamic_db_classes import DynamicDatabaseTestCase
from coding_systems.conftest import mock_migrate_coding_system
from coding_systems.icd10.import_data import import_data
from coding_systems.icd10.models import Concept
from coding_systems.versioning.models import CodingSystemRelease


MOCK_ICD10_IMPORT_DATA_PATH = (
    Path(__file__).parents[1]
    / "fixtures"
    / "import_resources"
    / "icd10_gastric_ulcer.zip"
)


class TestImportData(DynamicDatabaseTestCase):
    db_alias = "icd10_release-icd_20221001"
    import_data_path = MOCK_ICD10_IMPORT_DATA_PATH

    @pytest.mark.usefixtures("setup_coding_systems")
    def test_import_data(self):
        cs_release_count = CodingSystemRelease.objects.count()

        # import mock XML data
        # This consists of the just the concepts related to "Gastric ulcer", K25
        # Chapter - XI
        # Block - K20-31
        # Category - K25
        # 9 Modifiers - K25.0 - k25.9 (excl K25.8)
        with patch(
            "coding_systems.base.import_data_utils.call_command",
            mock_migrate_coding_system,
        ):
            import_data(
                self.import_data_path,
                release_name="release ICD",
                valid_from=date(2022, 10, 1),
                import_ref="Ref",
            )

        # A new CodingSystemRelease has been created
        assert CodingSystemRelease.objects.count() == cs_release_count + 1
        cs_release = CodingSystemRelease.objects.latest("id")
        assert cs_release.coding_system == "icd10"
        assert cs_release.release_name == "release ICD"
        assert cs_release.valid_from == date(2022, 10, 1)
        assert cs_release.import_ref == "Ref"

        assert cs_release.database_alias in settings.DATABASES
        concepts = Concept.objects.using(cs_release.database_alias).all()
        assert concepts.count() == 12
        assert set(concepts.values_list("code", flat=True)) == {
            "XI",
            "K20-K31",
            "K25",
            "K250",
            "K251",
            "K252",
            "K253",
            "K254",
            "K255",
            "K256",
            "K257",
            "K259",
        }
        chapter = concepts.get(code="XI")
        block = concepts.get(code="K20-K31")
        category = concepts.get(code="K25")
        subcategories = concepts.exclude(
            code__in={chapter.code, block.code, category.code}
        )

        assert chapter.parent is None
        assert block.parent == chapter
        assert category.parent == block
        for subcategory in subcategories:
            assert subcategory.parent == category
