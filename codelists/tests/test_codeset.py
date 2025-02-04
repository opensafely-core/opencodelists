import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from codelists.codeset import Codeset

from .codeset_test_data import examples
from .helpers import build_hierarchy, hierarchies


# build_hierarchy returns a hierarchy with the following structure:
#
#       a
#      / \
#     b   c
#    / \ / \
#   d   e   f
#  / \ / \ / \
# g   h   i   j


def id_fn(value):
    return value["description"]


@pytest.mark.parametrize("example", examples, ids=id_fn)
def test_from_codes(example):
    hierarchy = build_hierarchy()

    codeset = Codeset.from_codes(example["codes"], hierarchy)
    assert codeset.codes("+") == example["explicitly_included"]
    assert codeset.codes("-") == example["explicitly_excluded"]
    assert codeset.codes() == example["codes"]


@pytest.mark.parametrize("example", examples, ids=id_fn)
def test_codes(example):
    hierarchy = build_hierarchy()

    codeset = Codeset.from_definition(
        example["explicitly_included"],
        example["explicitly_excluded"],
        hierarchy,
    )
    assert codeset.codes("+") == example["explicitly_included"]
    assert codeset.codes("-") == example["explicitly_excluded"]
    assert codeset.codes() == example["codes"]


@pytest.mark.parametrize("example", examples, ids=id_fn)
def test_defining_tree(example):
    hierarchy = build_hierarchy()

    codeset = Codeset.from_definition(
        example["explicitly_included"],
        example["explicitly_excluded"],
        hierarchy,
    )
    assert codeset.defining_tree() == example["tree"]


@pytest.mark.parametrize("example", examples, ids=id_fn)
def test_walk_defining_tree(example):
    hierarchy = build_hierarchy()

    codeset = Codeset.from_definition(
        example["explicitly_included"],
        example["explicitly_excluded"],
        hierarchy,
    )
    assert list(codeset.walk_defining_tree(lambda x: x)) == example["tree_rows"]


def test_update():
    hierarchy = build_hierarchy()
    codeset = Codeset(
        {
            #        ?
            #       / \
            #      +   -
            #     / \ / \
            #   (+)  !  (-)
            #   / \ / \ / \
            # (+)  !   !  (-)
            "a": "?",
            "b": "+",
            "c": "-",
            "d": "(+)",
            "e": "!",
            "f": "(-)",
            "g": "(+)",
            "h": "!",
            "i": "!",
            "j": "(-)",
        },
        hierarchy,
    )

    updated_codeset = codeset.update([("a", "-"), ("f", "+"), ("b", "?"), ("a", "+")])
    assert updated_codeset.code_to_status == {
        #        +
        #       / \
        #     (+)  -
        #     / \ / \
        #   (+) (-)  +
        #   / \ / \ / \
        # (+) (-) (+) (+)
        "a": "+",
        "b": "(+)",
        "c": "-",
        "d": "(+)",
        "e": "(-)",
        "f": "+",
        "g": "(+)",
        "h": "(-)",
        "i": "(+)",
        "j": "(+)",
    }


@settings(deadline=None)
@given(hierarchies(24), st.sets(st.sampled_from(range(16))))
def test_roundtrip(hierarchy, codes):
    codeset = Codeset.from_codes(codes, hierarchy)
    assert codeset.codes() == codes
