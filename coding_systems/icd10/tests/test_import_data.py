from datetime import date
from unittest.mock import patch

import pytest
from django.conf import settings
from django.utils.text import slugify

from coding_systems.base.tests.dynamic_db_classes import DynamicDatabaseTestCase
from coding_systems.conftest import mock_migrate_coding_system
from coding_systems.icd10.claml_parser import ICD10Code
from coding_systems.icd10.import_data import import_release
from coding_systems.icd10.models import (
    Concept,
    ConceptEdition,
    ConceptRubric,
    ConceptUsage,
    DaggerAsteriskRelation,
    Edition,
    ModifierRubric,
    RubricKind,
)
from coding_systems.versioning.models import CodingSystemRelease


ICD10_CACHE_DIR = "/tmp/icd10-cache"
IMPORT_REF = "Ref"
# We need a separate db alias for each release we want to use in the tests.
# This dict maps from a test release name to the release_name and valid_from
# that will be used for the imported release.
IMPORT_RELEASES = {
    "vanilla": ("Vanilla ICD", date(2022, 10, 1)),
    "conflict": ("Conflict ICD", date(2022, 10, 2)),
    "dagger": ("Dagger ICD", date(2022, 10, 3)),
    "missing reference": ("Missing Reference ICD", date(2022, 10, 4)),
    "missing asterisk reference": (
        "Missing Asterisk Reference ICD",
        date(2022, 10, 4),
    ),
    "alterations": ("Alterations ICD", date(2022, 10, 5)),
    "invalid code": ("Invalid Code ICD", date(2022, 10, 5)),
    "missing parent": ("Missing Parent ICD", date(2022, 10, 6)),
    "rubrics": ("Rubrics ICD", date(2022, 10, 7)),
}


def import_release_metadata(name):
    release_name, valid_from = IMPORT_RELEASES[name]
    return {
        "release_name": release_name,
        "valid_from": valid_from,
        "import_ref": IMPORT_REF,
    }


def import_database_alias(name):
    release = import_release_metadata(name)
    return slugify(
        f"icd10_{release['release_name']}_{release['valid_from'].strftime('%Y%m%d')}"
    )


def code(
    code,
    parent=None,
    description="",
    usage=None,
    usage_pair_codes=None,
    term_modifier="",
    modifier_position=None,
    concept_rubrics=None,
    modifier_rubrics=None,
):
    return ICD10Code(
        code=code,
        description=description,
        usage=usage,
        usage_pair_codes=usage_pair_codes,
        parent=parent,
        term_modifier=term_modifier,
        modifier_position=modifier_position,
        concept_rubrics=concept_rubrics or {},
        modifier_rubrics=modifier_rubrics or {},
    )


class TestImportData(DynamicDatabaseTestCase):
    db_aliases = [import_database_alias(name) for name in IMPORT_RELEASES]

    def _parsed_output(self, parent_for_k25="K20-K31"):
        return {
            "XI": code("XI", description="Diseases of the digestive system"),
            "K20-K31": code(
                "K20-K31",
                description="Diseases of oesophagus, stomach and duodenum",
                parent="XI",
            ),
            "K25": code("K25", description="Gastric ulcer", parent=parent_for_k25),
            "K250": code(
                code="K250",
                description="Gastric ulcer",
                parent="K25",
                term_modifier="Acute with haemorrhage",
                modifier_position=4,
            ),
            "K251": code(
                code="K251",
                description="Gastric ulcer",
                parent="K25",
                term_modifier="Acute with perforation",
                modifier_position=4,
            ),
        }

    def _parsed_2019_output(self, parent_for_k25="K20-K31"):
        parsed = self._parsed_output(parent_for_k25)
        parsed["K252"] = code(
            code="K252",
            description="Gastric ulcer",
            parent="K25",
            term_modifier="Acute with both haemorrhage and perforation",
            modifier_position=4,
        )
        return parsed

    def _import_records(self, release, output_2016=None, output_2019=None):
        if output_2016 is None:
            output_2016 = self._parsed_output()
        if output_2019 is None:
            output_2019 = self._parsed_2019_output()

        with (
            patch(
                "coding_systems.icd10.import_data.load_import_records",
                return_value=(output_2016, output_2019),
            ) as load_import_records,
            patch(
                "coding_systems.base.import_data_utils.call_command",
                mock_migrate_coding_system,
            ),
        ):
            import_release(ICD10_CACHE_DIR, **import_release_metadata(release))

        return load_import_records

    @pytest.mark.usefixtures("setup_coding_systems")
    def test_import_data(self):
        cs_release_count = CodingSystemRelease.objects.count()

        release_to_import = "vanilla"

        load_import_records = self._import_records(release_to_import)

        load_import_records.assert_called_once_with(ICD10_CACHE_DIR, None)
        assert CodingSystemRelease.objects.count() == cs_release_count + 1
        cs_release = CodingSystemRelease.objects.latest("id")
        assert cs_release.coding_system == "icd10"
        assert cs_release.release_name == IMPORT_RELEASES[release_to_import][0]
        assert cs_release.valid_from == IMPORT_RELEASES[release_to_import][1]
        assert cs_release.import_ref == IMPORT_REF

        assert cs_release.database_alias in settings.DATABASES
        editions = Edition.objects.using(cs_release.database_alias).order_by("year")
        assert list(editions.values_list("id", "year")) == [
            ("2016", 2016),
            ("2019", 2019),
        ]

        concepts = Concept.objects.using(cs_release.database_alias).all()
        assert concepts.count() == 6
        assert set(concepts.values_list("code", flat=True)) == {
            "XI",
            "K20-K31",
            "K25",
            "K250",
            "K251",
            "K252",
        }

        concept_editions = ConceptEdition.objects.using(cs_release.database_alias).all()
        assert concept_editions.count() == 11
        assert set(concept_editions.values_list("term", "term_modifier")) == {
            ("Gastric ulcer", "Acute with both haemorrhage and perforation"),
            ("Diseases of oesophagus, stomach and duodenum", ""),
            ("Diseases of the digestive system", ""),
            ("Gastric ulcer", "Acute with perforation"),
            ("Gastric ulcer", "Acute with haemorrhage"),
            ("Gastric ulcer", ""),
        }
        assert set(
            concept_editions.filter(edition_id="2016").values_list(
                "concept_id", flat=True
            )
        ) == {"XI", "K20-K31", "K25", "K250", "K251"}
        assert set(
            concept_editions.filter(edition_id="2019").values_list(
                "concept_id", flat=True
            )
        ) == {"XI", "K20-K31", "K25", "K250", "K251", "K252"}

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

        assert (
            DaggerAsteriskRelation.objects.using(cs_release.database_alias).count() == 0
        )

    @pytest.mark.usefixtures("setup_coding_systems")
    def test_import_data_uses_release_builder_records_for_2016_only(self):
        output_2016 = self._parsed_output()
        output_2016["K253"] = code(
            code="K253",
            description="Builder-only 2016 record",
            parent="K25",
        )

        self._import_records("alterations", output_2016)

        cs_release = CodingSystemRelease.objects.latest("id")
        assert set(
            ConceptEdition.objects.using(cs_release.database_alias)
            .filter(edition_id="2016")
            .values_list("concept_id", flat=True)
        ) == {"XI", "K20-K31", "K25", "K250", "K251", "K253"}
        assert set(
            ConceptEdition.objects.using(cs_release.database_alias)
            .filter(edition_id="2019")
            .values_list("concept_id", flat=True)
        ) == {"XI", "K20-K31", "K25", "K250", "K251", "K252"}

    @pytest.mark.usefixtures("setup_coding_systems")
    def test_import_data_creates_dagger_asterisk_relations_per_edition(self):
        output_2016 = self._parsed_output()
        output_2016["K250"].usage = ConceptUsage.DAGGER
        output_2016["K250"].usage_pair_codes = ("K251",)
        output_2016["K251"].usage = ConceptUsage.ASTERISK
        output_2016["K251"].usage_pair_codes = ("K250",)
        output_2019 = self._parsed_output()
        output_2019["K251"].usage = ConceptUsage.ASTERISK
        output_2019["K251"].usage_pair_codes = ("K250",)

        self._import_records("dagger", output_2016, output_2019)

        cs_release = CodingSystemRelease.objects.latest("id")
        relations = DaggerAsteriskRelation.objects.using(
            cs_release.database_alias
        ).select_related("dagger_concept", "asterisk_concept")

        assert relations.count() == 2
        assert {
            (
                relation.dagger_concept.edition_id,
                relation.dagger_concept.concept_id,
                relation.dagger_code,
                relation.asterisk_concept.concept_id,
                relation.asterisk_code,
            )
            for relation in relations
        } == {
            ("2016", "K250", "K250", "K251", "K251"),
            ("2019", "K250", "K250", "K251", "K251"),
        }

    @pytest.mark.usefixtures("setup_coding_systems")
    def test_import_data_creates_rubrics(self):
        output_2016 = self._parsed_output()
        output_2016["K25"].concept_rubrics = {
            RubricKind.PREFERRED: ["Gastric ulcer"],
            RubricKind.INCLUSION: ["Erosion (acute) of stomach"],
        }
        output_2016["K250"].modifier_rubrics = {
            RubricKind.PREFERRED: ["Acute with haemorrhage"],
            RubricKind.NOTE: ["Includes bleeding"],
        }

        self._import_records("rubrics", output_2016, self._parsed_output())

        cs_release = CodingSystemRelease.objects.latest("id")
        concept_rubrics = ConceptRubric.objects.using(
            cs_release.database_alias
        ).select_related("concept_edition")
        modifier_rubrics = ModifierRubric.objects.using(
            cs_release.database_alias
        ).select_related("concept_edition")

        assert {
            (
                rubric.concept_edition.edition_id,
                rubric.concept_edition.concept_id,
                rubric.kind,
                rubric.text,
            )
            for rubric in concept_rubrics
        } == {
            ("2016", "K25", RubricKind.PREFERRED, "Gastric ulcer"),
            ("2016", "K25", RubricKind.INCLUSION, "Erosion (acute) of stomach"),
        }
        assert {
            (
                rubric.concept_edition.edition_id,
                rubric.concept_edition.concept_id,
                rubric.kind,
                rubric.text,
            )
            for rubric in modifier_rubrics
        } == {
            ("2016", "K250", RubricKind.PREFERRED, "Acute with haemorrhage"),
            ("2016", "K250", RubricKind.NOTE, "Includes bleeding"),
        }

    @pytest.mark.usefixtures("setup_coding_systems")
    def test_import_data_fails_on_parent_conflict(self):
        with pytest.raises(ValueError, match="Conflicting parent for ICD-10 code K25"):
            self._import_records(
                "conflict",
                self._parsed_output(),
                self._parsed_2019_output(parent_for_k25="XI"),
            )

    @pytest.mark.usefixtures("setup_coding_systems")
    def test_import_data_preserves_missing_usage_reference_as_raw_code(self):
        output_2016 = self._parsed_output()
        output_2016["K250"].usage = ConceptUsage.DAGGER
        output_2016["K250"].usage_pair_codes = ("K259",)

        self._import_records(
            "missing asterisk reference", output_2016, self._parsed_output()
        )

        cs_release = CodingSystemRelease.objects.latest("id")
        relation = DaggerAsteriskRelation.objects.using(cs_release.database_alias).get()

        assert (
            relation.dagger_concept.edition_id,
            relation.dagger_concept.concept_id,
            relation.dagger_code,
            relation.asterisk_concept,
            relation.asterisk_code,
        ) == (
            "2016",
            "K250",
            "K250",
            None,
            "K259",
        )

    @pytest.mark.usefixtures("setup_coding_systems")
    def test_import_data_preserves_missing_dagger_usage_reference_as_raw_code(self):
        output_2016 = self._parsed_output()
        output_2016["K251"].usage = ConceptUsage.ASTERISK
        output_2016["K251"].usage_pair_codes = ("K259",)

        self._import_records("missing reference", output_2016, self._parsed_output())

        cs_release = CodingSystemRelease.objects.latest("id")
        relation = DaggerAsteriskRelation.objects.using(cs_release.database_alias).get()

        assert (
            relation.dagger_concept,
            relation.dagger_code,
            relation.asterisk_concept.edition_id,
            relation.asterisk_concept.concept_id,
            relation.asterisk_code,
        ) == (
            None,
            "K259",
            "2016",
            "K251",
            "K251",
        )

    @pytest.mark.usefixtures("setup_coding_systems")
    def test_import_data_fails_on_missing_parent(self):
        output_2016 = self._parsed_output()
        output_2016["K259"] = code(
            code="K259",
            parent="K99",
        )

        with pytest.raises(
            ValueError, match="Parent K99 for ICD-10 code K259 was not imported"
        ):
            self._import_records("missing parent", output_2016)

    # test that a code that doesn't match the expected format throws an error
    @pytest.mark.usefixtures("setup_coding_systems")
    def test_import_data_fails_on_code_format(self):
        output_2016 = self._parsed_output()
        output_2016["INVALID_CODE"] = code("INVALID_CODE")

        with pytest.raises(
            ValueError, match="Unrecognised ICD-10 code format: INVALID_CODE"
        ):
            self._import_records("invalid code", output_2016)
