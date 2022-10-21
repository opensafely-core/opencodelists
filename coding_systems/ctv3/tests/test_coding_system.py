import pytest

from coding_systems.ctv3.coding_system import CodingSystem
from coding_systems.ctv3.models import TPPConcept, TPPRelationship


@pytest.fixture
def coding_system():
    yield CodingSystem(database_alias="ctv3_test_20200101")


def test_lookup_names(coding_system):
    for code in [".....", "11111", "22222"]:
        TPPConcept.objects.using("ctv3_test_20200101").create(
            read_code=code, description=f"Concept {code}"
        )

    assert coding_system.lookup_names(["11111", "22222", "99999"]) == {
        "11111": "Concept 11111",
        "22222": "Concept 22222",
    }


def test_code_to_term(coding_system):
    for code in [".....", "11111", "22222"]:
        TPPConcept.objects.using("ctv3_test_20200101").create(
            read_code=code, description=f"Concept {code}"
        )

    assert coding_system.code_to_term(["11111", "22222", "99999"]) == {
        "11111": "Concept 11111",
        "22222": "Concept 22222",
        "99999": "Unknown",
    }


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
