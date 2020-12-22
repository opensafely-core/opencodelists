from hypothesis import given, settings
from hypothesis import strategies as st

from codelists.definition2 import Definition2

from .definition_test_data import examples
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
            definition = Definition2.from_codes(example["codes"], hierarchy)
            assert definition.explicitly_included == example["explicitly_included"]
            assert definition.explicitly_excluded == example["explicitly_excluded"]
            assert definition.codes(hierarchy) == example["codes"]


def test_codes(subtests):
    hierarchy = build_hierarchy()

    for example in examples:
        with subtests.test(example["description"]):
            definition = Definition2(
                example["explicitly_included"], example["explicitly_excluded"]
            )
            assert definition.explicitly_included == example["explicitly_included"]
            assert definition.explicitly_excluded == example["explicitly_excluded"]
            assert definition.codes(hierarchy) == example["codes"]


def test_tree(subtests):
    hierarchy = build_hierarchy()

    for example in examples:
        with subtests.test(example["description"]):
            definition = Definition2(
                example["explicitly_included"], example["explicitly_excluded"]
            )
            assert definition.tree(hierarchy) == example["tree"]


@settings(deadline=None)
@given(hierarchies(24), st.sets(st.sampled_from(range(16))))
def test_roundtrip(hierarchy, codes):
    definition = Definition2.from_codes(codes, hierarchy)
    assert definition.codes(hierarchy) == codes


@settings(deadline=None)
@given(hierarchies(24), st.sets(st.sampled_from(range(16))))
def test_code_to_status(hierarchy, codes):
    definition = Definition2.from_codes(codes, hierarchy)
    code_to_status = definition.code_to_status(hierarchy)
    explicitly_included = {
        code for code, status in code_to_status.items() if status == "+"
    }
    assert explicitly_included == definition.explicitly_included
    explicitly_excluded = {
        code for code, status in code_to_status.items() if status == "-"
    }
    assert explicitly_excluded == definition.explicitly_excluded
