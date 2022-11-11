import pytest

from coding_systems.ctv3.coding_system import CodingSystem
from coding_systems.ctv3.models import (
    RawConcept,
    RawConceptTermMapping,
    RawTerm,
    TPPConcept,
    TPPRelationship,
)


@pytest.fixture
def coding_system():
    yield CodingSystem(database_alias="ctv3_test_20200101")


@pytest.fixture
def tpp_concepts():
    for code in [".....", "11111", "22222"]:
        TPPConcept.objects.using("ctv3_test_20200101").create(
            read_code=code, description=f"Concept {code}"
        )


@pytest.fixture
def raw_concepts():
    for raw_code in ["33333", "44444"]:
        rawconcept = RawConcept.objects.using("ctv3_test_20200101").create(
            read_code=raw_code,
            status="C",
            unknown_field_2="A",
            another_concept_id=raw_code,
        )
        rawterm = RawTerm.objects.using("ctv3_test_20200101").create(
            term_id=raw_code, status="C", name_1=f"raw_concept_{raw_code}"
        )
        RawConceptTermMapping.objects.using("ctv3_test_20200101").create(
            concept=rawconcept, term=rawterm, term_type="P"
        )


def test_lookup_names(coding_system, tpp_concepts):
    assert coding_system.lookup_names(["11111", "22222", "99999"]) == {
        "11111": "Concept 11111",
        "22222": "Concept 22222",
    }


def test_code_to_term(coding_system, tpp_concepts):
    assert coding_system.code_to_term(["11111", "22222", "99999"]) == {
        "11111": "Concept 11111",
        "22222": "Concept 22222",
        "99999": "Unknown",
    }


def test_search_by_term(coding_system, tpp_concepts, raw_concepts):
    # searching by "concept" matches all concepts, both raw and tpp
    assert coding_system.search_by_term("concept") == {
        ".....",
        "11111",
        "22222",
        "33333",
        "44444",
    }
    # searching by "raw_concept" matches only the raw ones
    assert coding_system.search_by_term("raw_concept") == {"33333", "44444"}
    # search by an unknown term
    assert coding_system.search_by_term("unk") == set()


def test_search_by_code(coding_system, tpp_concepts, raw_concepts):
    # search by a TPP concept code
    assert coding_system.search_by_code("22222") == {"22222"}
    # search by a raw code
    assert coding_system.search_by_code("44444") == {"44444"}
    # search by an unknown code
    assert coding_system.search_by_code("55555") == set()


def test_relationships(coding_system):
    r"""Hierarchy has this structure:
        .
       / \
      1   2
     / \ / \
    3   4   5
    """

    records = [
        [".....", "11111", 1],
        [".....", "22222", 1],
        [".....", "33333", 2],
        [".....", "44444", 2],
        [".....", "44444", 2],  # There are two routes from ..... to 44444
        [".....", "55555", 2],
        ["11111", "33333", 1],
        ["11111", "44444", 1],
        ["22222", "44444", 1],
        ["22222", "55555", 1],
    ]

    for ancestor_code, descendant_code, distance in records:
        ancestor, _ = TPPConcept.objects.using("ctv3_test_20200101").get_or_create(
            read_code=ancestor_code, defaults={"description": ancestor_code}
        )
        descendant, _ = TPPConcept.objects.using("ctv3_test_20200101").get_or_create(
            read_code=descendant_code, defaults={"description": descendant_code}
        )
        TPPRelationship.objects.using("ctv3_test_20200101").create(
            ancestor=ancestor,
            descendant=descendant,
            distance=distance,
        )

    assert set(coding_system.ancestor_relationships(["....."])) == set()

    assert set(coding_system.ancestor_relationships(["11111"])) == {
        (".....", "11111"),
    }

    assert set(coding_system.ancestor_relationships(["33333", "55555"])) == {
        (".....", "11111"),
        (".....", "22222"),
        ("11111", "33333"),
        ("22222", "55555"),
    }

    assert set(coding_system.descendant_relationships(["....."])) == {
        (".....", "11111"),
        (".....", "22222"),
        ("11111", "33333"),
        ("11111", "44444"),
        ("22222", "44444"),
        ("22222", "55555"),
    }

    assert set(coding_system.descendant_relationships(["11111"])) == {
        ("11111", "33333"),
        ("11111", "44444"),
    }

    assert set(coding_system.descendant_relationships(["33333", "55555"])) == set()
