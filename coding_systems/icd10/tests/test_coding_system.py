import pytest

from coding_systems.icd10.coding_system import CodingSystem
from coding_systems.icd10.models import ConceptRubric, ModifierRubric, RubricKind


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


def test_lookup_names_uses_latest_matching_term(monkeypatch, coding_system):
    class FakeQuerySet:
        def filter(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def values_list(self, *args, **kwargs):
            return [
                ("B59", "Newer term", None),
                ("B59", "Older term", None),
                ("M77", "Other enthesopathies", None),
            ]

    class FakeManager:
        def using(self, alias):
            return FakeQuerySet()

    monkeypatch.setattr(
        "coding_systems.icd10.coding_system.ConceptEdition.objects",
        FakeManager(),
    )

    assert coding_system.lookup_names(["B59", "M77"]) == {
        "B59": "Newer term",
        "M77": "Other enthesopathies",
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
