import pytest

from coding_systems.icd10.coding_system import CodingSystem
from coding_systems.icd10.models import (
    Concept,
    ConceptEdition,
    ConceptKind,
    ConceptRubric,
    ConceptUsage,
    Edition,
    ModifierRubric,
    RubricKind,
)


@pytest.fixture
def coding_system():
    yield CodingSystem(database_alias="icd10_test_20200101")


def test_codes_by_type(icd10_data, coding_system):
    assert coding_system.codes_by_type(
        ["A771", "XIII", "M60-M79", "M70-M79", "M77", "M770", "M779"], None
    ) == {
        "I: Certain infectious and parasitic diseases": ["A771"],
        "XIII: Diseases of the musculoskeletal system and connective tissue": [
            "XIII",
            "M60-M79",
            "M70-M79",
            "M77",
            "M770",
            "M779",
        ],
    }


def test_lookup_names(icd10_data, coding_system):
    assert coding_system.lookup_names(["M77", "M770", "99999"]) == {
        "M77": "Other enthesopathies",
        "M770": "Medial epicondylitis",
    }


def test_code_to_term(icd10_data, coding_system):
    assert coding_system.code_to_term(["M77", "M770", "M7700", "99999"]) == {
        "M77": "Other enthesopathies",
        "M770": "Medial epicondylitis",
        "M7700": "Medial epicondylitis : Multiple sites",
        "99999": "Unknown",
    }


def test_lookup_names_prefers_2016_term(icd10_data, coding_system):
    edition_2016 = Edition.objects.using(coding_system.database_alias).create(
        id="2016",
        version=20160101,
        year=2016,
        source_description="test 2016",
    )
    edition_2019 = Edition.objects.using(coding_system.database_alias).create(
        id="2019",
        version=20190101,
        year=2019,
        source_description="test 2019",
    )
    concept = Concept.objects.using(coding_system.database_alias).create(code="B59")

    ConceptEdition.objects.using(coding_system.database_alias).create(
        concept=concept,
        edition=edition_2019,
        kind=ConceptKind.CATEGORY,
        usage=ConceptUsage.NORMAL,
        term="Newer 2019 term",
    )
    ConceptEdition.objects.using(coding_system.database_alias).create(
        concept=concept,
        edition=edition_2016,
        kind=ConceptKind.CATEGORY,
        usage=ConceptUsage.NORMAL,
        term="Preferred 2016 term",
    )

    assert coding_system.lookup_names(["B59", "M77"]) == {
        "B59": "Preferred 2016 term",
        "M77": "Other enthesopathies",
    }


def test_lookup_names_uses_latest_term_when_2016_term_does_not_exist(
    icd10_data, coding_system
):
    edition_2019 = Edition.objects.using(coding_system.database_alias).create(
        id="2019",
        version=20190101,
        year=2019,
        source_description="test 2019",
    )
    edition_2020 = Edition.objects.using(coding_system.database_alias).create(
        id="2020",
        version=20200101,
        year=2020,
        source_description="test 2020",
    )
    concept = Concept.objects.using(coding_system.database_alias).create(code="B59")

    ConceptEdition.objects.using(coding_system.database_alias).create(
        concept=concept,
        edition=edition_2019,
        kind=ConceptKind.CATEGORY,
        usage=ConceptUsage.NORMAL,
        term="Older 2019 term",
    )
    ConceptEdition.objects.using(coding_system.database_alias).create(
        concept=concept,
        edition=edition_2020,
        kind=ConceptKind.CATEGORY,
        usage=ConceptUsage.NORMAL,
        term="Latest 2020 term",
    )

    assert coding_system.lookup_names(["B59"]) == {
        "B59": "Latest 2020 term",
    }


def test_matching_codes(icd10_data, coding_system):
    assert coding_system.matching_codes(["M77", "M770", "99999"]) == {"M77", "M770"}


def test_search_by_term(icd10_data, coding_system):
    assert coding_system.search_by_term("rickett") == {
        "A77",
        "A770",
        "A771",
        "A772",
        "A773",
    }


def test_search_by_term_includes_inclusion_rubric_match(coding_system):
    # Real-world pattern: 2016 has Causalgia as a term on G564,
    # while 2019 has Causalgia as an inclusion rubric on G906.
    edition_2016 = Edition.objects.using(coding_system.database_alias).create(
        id="20160101",
        version=20160101,
        year=2016,
        source_description="test 2016",
    )
    edition_2019 = Edition.objects.using(coding_system.database_alias).create(
        id="20190101",
        version=20190101,
        year=2019,
        source_description="test 2019",
    )

    g564 = Concept.objects.using(coding_system.database_alias).create(code="G564")
    g906 = Concept.objects.using(coding_system.database_alias).create(code="G906")

    ConceptEdition.objects.using(coding_system.database_alias).create(
        concept=g564,
        edition=edition_2016,
        kind=ConceptKind.CATEGORY,
        usage=ConceptUsage.NORMAL,
        term="Causalgia",
    )
    g906_2019 = ConceptEdition.objects.using(coding_system.database_alias).create(
        concept=g906,
        edition=edition_2019,
        kind=ConceptKind.CATEGORY,
        usage=ConceptUsage.NORMAL,
        term="Complex regional pain syndrome type II",
    )
    ConceptRubric.objects.using(coding_system.database_alias).create(
        concept_edition=g906_2019,
        kind=RubricKind.INCLUSION,
        text="Causalgia",
    )

    assert coding_system.search_by_term("Causalgia") == {"G564", "G906"}


def test_search_by_code_exact(icd10_data, coding_system):
    assert coding_system.search_by_code("A77") == {"A77"}


def test_search_by_code_wildcard(icd10_data, coding_system):
    assert coding_system.search_by_code("A77*") == {
        "A77",
        "A770",
        "A771",
        "A772",
        "A773",
        "A778",
        "A779",
    }


def test_ancestor_relationships(icd10_data, coding_system):
    assert coding_system.ancestor_relationships({"A770"}) == [
        ("A77", "A770"),
        ("A75-A79", "A77"),
        ("I", "A75-A79"),
        (None, "I"),
    ]


def test_descendant_relationships(icd10_data, coding_system):
    assert coding_system.descendant_relationships({"I"}) == [
        ("I", "A75-A79"),
        ("A75-A79", "A77"),
        ("A77", "A770"),
        ("A77", "A771"),
        ("A77", "A772"),
        ("A77", "A773"),
        ("A77", "A778"),
        ("A77", "A779"),
    ]


def test_lookup_additional_rubrics_for_concept_code(icd10_data, coding_system):
    ConceptRubric.objects.using(coding_system.database_alias).create(
        concept_edition_id=13,
        kind=RubricKind.INCLUSION,
        text="Golfer's elbow",
    )

    assert coding_system.lookup_additional_rubrics(["M770"])["rubrics"] == {
        "M770": {
            "concept_rubrics": {RubricKind.INCLUSION: ["Golfer's elbow"]},
            "modifier_rubrics": {},
        }
    }


def test_lookup_additional_rubrics_with_no_codes(coding_system):
    assert coding_system.lookup_additional_rubrics([])["rubrics"] == {}


def test_lookup_additional_rubrics_for_modifier_code_includes_parent_concept_rubrics(
    icd10_data, coding_system
):
    ConceptRubric.objects.using(coding_system.database_alias).create(
        concept_edition_id=13,
        kind=RubricKind.INCLUSION,
        text="Golfer's elbow",
    )
    ModifierRubric.objects.using(coding_system.database_alias).create(
        concept_edition_id=22,
        kind=RubricKind.NOTE,
        text="Includes multiple sites",
    )

    assert coding_system.lookup_additional_rubrics(["M7700"])["rubrics"] == {
        "M7700": {
            "concept_rubrics": {RubricKind.INCLUSION: ["Golfer's elbow"]},
            "modifier_rubrics": {
                "Multiple sites": {RubricKind.NOTE: ["Includes multiple sites"]}
            },
        }
    }


def test_term_differences(icd10_data, coding_system):

    x590 = coding_system.lookup_additional_rubrics(["X590"])
    xxxx = coding_system.lookup_additional_rubrics(["XXXX"])
    blank = coding_system.lookup_additional_rubrics([])

    assert "term_differences" in x590
    assert "X590" in x590["term_differences"]
    assert not x590["term_differences"]["X590"]["equivalent"]

    assert "term_differences" in xxxx
    assert xxxx["term_differences"] == {}

    assert "term_differences" in blank
    assert blank["term_differences"] == {}


def test_lookup_dagger_asterisk_usages_with_no_codes(coding_system):
    assert coding_system.lookup_dagger_asterisk_usages([]) == {}


@pytest.mark.parametrize("asterisk_usage", [ConceptUsage.ASTERISK, "aster"])
def test_lookup_dagger_asterisk_usages(icd10_data, coding_system, asterisk_usage):
    ConceptEdition.objects.using(coding_system.database_alias).filter(id=12).update(
        usage=ConceptUsage.DAGGER
    )
    ConceptEdition.objects.using(coding_system.database_alias).filter(id=13).update(
        usage=ConceptUsage.DAGGER
    )
    ConceptEdition.objects.using(coding_system.database_alias).filter(id=14).update(
        usage=asterisk_usage
    )

    assert coding_system.lookup_dagger_asterisk_usages(
        ["M77", "M770", "M771", "M772"]
    ) == {
        "M77": {
            "usage": "dagger",
            "url": "https://icd.who.int/browse10/2019/en#/M77",
        },
        "M770": {
            "usage": "dagger",
            "url": "https://icd.who.int/browse10/2019/en#/M77.0",
        },
        "M771": {
            "usage": "asterisk",
            "url": "https://icd.who.int/browse10/2019/en#/M77.1",
        },
    }
