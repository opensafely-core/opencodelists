from hypothesis import given, settings
from hypothesis import strategies as st

from codelists.definition2 import Definition2

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

examples = [
    ("a", "a", "bc", "root element only"),
    ("b", "b", "de", "intermediate element only"),
    ("g", "g", "", "leaf element only"),
    ("abcdefghij", "a", "", "root element + descendants"),
    ("abcdfghij", "ahi", "e", "root element + all descendants except intermediate"),
    ("abcdefghi", "a", "j", "root element + all descendants except leaf"),
    ("bdeghi", "b", "", "intermediate element + descendants"),
    ("bdegh", "b", "i", "intermediate element + all descendants except leaf"),
    ("abdeghi", "ae", "c", "root element + descendants of intermediate element"),
    ("abdg", "a", "c", "root element - descendants of intermediate element"),
]


def test_from_codes(subtests):
    hierarchy = build_hierarchy()

    for codes, included_ancestors, excluded_ancestors, subtest_name in examples:
        codes = set(codes)
        included_ancestors = set(included_ancestors)
        excluded_ancestors = set(excluded_ancestors)

        with subtests.test(subtest_name):
            definition = Definition2.from_codes(codes, hierarchy)
            assert definition.included_ancestors == included_ancestors
            assert definition.excluded_ancestors == excluded_ancestors
            assert definition.codes(hierarchy) == codes


def test_codes(subtests):
    hierarchy = build_hierarchy()

    for codes, included_ancestors, excluded_ancestors, subtest_name in examples:
        codes = set(codes)
        included_ancestors = set(included_ancestors)
        excluded_ancestors = set(excluded_ancestors)

        with subtests.test(subtest_name):
            definition = Definition2(included_ancestors, excluded_ancestors)
            assert definition.included_ancestors == included_ancestors
            assert definition.excluded_ancestors == excluded_ancestors
            assert definition.codes(hierarchy) == codes


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
    included_ancestors = {
        code for code, status in code_to_status.items() if status == "+"
    }
    assert included_ancestors == definition.included_ancestors
    excluded_ancestors = {
        code for code, status in code_to_status.items() if status == "-"
    }
    assert excluded_ancestors == definition.excluded_ancestors
