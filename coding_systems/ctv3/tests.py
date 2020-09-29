from coding_systems.ctv3.coding_system import (
    ancestor_relationships,
    descendant_relationships,
)
from coding_systems.ctv3.models import TPPConcept, TPPRelationship


def test_relationships():
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
        ancestor, _ = TPPConcept.objects.get_or_create(
            read_code=ancestor_code, defaults={"description": ancestor_code}
        )
        descendant, _ = TPPConcept.objects.get_or_create(
            read_code=descendant_code, defaults={"description": descendant_code}
        )
        TPPRelationship.objects.create(
            ancestor=ancestor, descendant=descendant, distance=distance
        )

    assert set(ancestor_relationships(["....."])) == set()

    assert set(ancestor_relationships(["11111"])) == {
        (".....", "11111"),
    }

    assert set(ancestor_relationships(["33333", "55555"])) == {
        (".....", "11111"),
        (".....", "22222"),
        ("11111", "33333"),
        ("22222", "55555"),
    }

    assert set(descendant_relationships(["....."])) == {
        (".....", "11111"),
        (".....", "22222"),
        ("11111", "33333"),
        ("11111", "44444"),
        ("22222", "44444"),
        ("22222", "55555"),
    }

    assert set(descendant_relationships(["11111"])) == {
        ("11111", "33333"),
        ("11111", "44444"),
    }

    assert set(descendant_relationships(["33333", "55555"])) == set()
