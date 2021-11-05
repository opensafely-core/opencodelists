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


def test_from_codes(subtests):
    hierarchy = build_hierarchy()

    for example in examples:
        with subtests.test(example["description"]):
            codeset = Codeset.from_codes(example["codes"], hierarchy)
            assert codeset.codes("+") == example["explicitly_included"]
            assert codeset.codes("-") == example["explicitly_excluded"]
            assert codeset.codes() == example["codes"]


def test_codes(subtests):
    hierarchy = build_hierarchy()

    for example in examples:
        with subtests.test(example["description"]):
            codeset = Codeset.from_definition(
                example["explicitly_included"],
                example["explicitly_excluded"],
                hierarchy,
            )
            assert codeset.codes("+") == example["explicitly_included"]
            assert codeset.codes("-") == example["explicitly_excluded"]
            assert codeset.codes() == example["codes"]


def test_defining_tree(subtests):
    hierarchy = build_hierarchy()

    for example in examples:
        with subtests.test(example["description"]):
            codeset = Codeset.from_definition(
                example["explicitly_included"],
                example["explicitly_excluded"],
                hierarchy,
            )
            assert codeset.defining_tree() == example["tree"]


def test_walk_defining_tree(subtests):
    hierarchy = build_hierarchy()

    for example in examples:
        with subtests.test(example["description"]):
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


def test_remove():
    hierarchy = build_hierarchy()
    #       a
    #      / \
    #     b   c
    #    / \ / \
    #   d   e   f
    #  / \ / \ / \
    # g   h   i   j

    codeset = Codeset(
        {
            #        +
            #       / \
            #      +   -
            #     / \ / \
            #   (+)  !  (-)
            #   / \ / \ / \
            # (+)  !   !  (-)
            "a": "+",
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

    # If we remove a defining code with no ancestors, the defining code is removed from
    # the new codeset.
    new_codeset = codeset.remove({"a"})
    assert new_codeset.code_to_status == {
        #        .
        #       / \
        #      +   -
        #     / \ / \
        #   (+)  !  (-)
        #   / \ / \ / \
        # (+)  !   !  (-)
        "b": "+",
        "c": "-",
        "d": "(+)",
        "e": "!",
        "f": "(-)",
        "g": "(+)",
        "h": "!",
        "i": "!",
        "j": "(-)",
    }

    # If we remove all non-defining codes, nothing is actually removed from the new
    # codeset.
    new_codeset = codeset.remove({"d", "e", "f", "g", "h", "i", "j"})
    assert new_codeset.code_to_status == codeset.code_to_status

    new_codeset = codeset.remove({"a", "b"})
    assert new_codeset.code_to_status == {
        #        .
        #       / \
        #      .   -
        #     / \ / \
        #    +  (-) (-)
        #   / \ / \ / \
        # (+) (-) (-) (-)
        "c": "-",
        "d": "+",
        "e": "(-)",
        "f": "(-)",
        "g": "(+)",
        "h": "(-)",
        "i": "(-)",
        "j": "(-)",
    }


# @settings(deadline=None)
# @given(hierarchies(24), st.sets(st.sampled_from(range(24))))
# def test_valid(hierarchy, codes):
#     codeset = Codeset.from_codes(codes, hierarchy)
#     assert_valid(codeset, hierarchy)


@settings(deadline=None)
@given(hierarchies(24), st.sets(st.sampled_from(range(24))))
def test_roundtrip(hierarchy, codes):
    codeset = Codeset.from_codes(codes, hierarchy)
    assert codeset.codes() == codes


# @settings(deadline=None)
# @given(
#     hierarchies(24),
#     st.sets(st.sampled_from(range(24))),
#     st.sets(st.sampled_from(range(24))),
# )
# def test_remove(hierarchy, codeset_codes, codes_to_remove):
#     codes_to_remove = codes_to_remove & codeset_codes
#     codeset = Codeset.from_codes(codeset_codes, hierarchy)
#     new_codeset = codeset.remove(codes_to_remove)
#     assert_valid(new_codeset, hierarchy)


# def assert_valid(codeset, hierarchy):
#     all_codes = codeset.all_codes()
#     for code in all_codes:
#         for descendant in hierarchy.descendants(code):
#             assert descendant in all_codes
