from unittest import TestCase

from hypothesis import given, settings
from hypothesis import strategies as st

from codelists.definition import Definition
from codelists.hierarchy import Hierarchy


@st.composite
def hierarchies(draw, size):
    """Build a Hierarchy with `size` nodes.

    Based on an indea by @Zac-HD at https://github.com/HypothesisWorks/hypothesis/issues/2464.
    """

    edges = []
    for child_id in range(1, size):
        for parent_id in draw(st.sets(st.sampled_from(range(child_id)), min_size=1)):
            edges.append((parent_id, child_id))
    return Hierarchy("0", edges)


class DefinitionTests(TestCase):
    def test_roundtrip_examples(self):
        # tree has this structure:
        #
        #      ┌--0--┐
        #      |     |
        #   ┌--1--┌--2--┐
        #   |     |     |
        # ┌-3-┐ ┌-4-┐ ┌-5-┐
        # |   | |   | |   |
        # 6   7 8   9 10 11

        edges = [
            ("0", "1"),
            ("0", "2"),
            ("1", "3"),
            ("1", "4"),
            ("2", "4"),
            ("2", "5"),
            ("3", "6"),
            ("3", "7"),
            ("4", "8"),
            ("4", "9"),
            ("5", "10"),
            ("5", "11"),
        ]
        hierarchy = Hierarchy("0", edges)

        for codes, query in [
            # the root element
            ({"0"}, ["0"]),
            # an intermediate element
            ({"2"}, ["2"]),
            # a leaf element
            ({"8"}, ["8"]),
            # everything under intermediate element, inclusive
            ({"2", "4", "5", "8", "9", "10", "11"}, ["2<"]),
            # everything under intermediate element, exclusive
            ({"4", "5", "8", "9", "10", "11"}, ["4<", "5<"]),
            # everything under intermediate element, except another intermediate element
            ({"2", "5", "8", "9", "10", "11"}, ["2<", "~4"]),
            # everything under intermediate element, except leaf element
            ({"2", "4", "5", "9", "10", "11"}, ["2<", "~8"]),
            # everything under root element, except intermediate element and its children (i)
            ({"0", "1", "2", "3", "4", "6", "7", "8", "9"}, ["0", "1<", "2"]),
            # everything under root element, except intermediate element and its children (ii)
            (
                {"0", "1", "2", "3", "5", "6", "7", "10", "11"},
                ["0", "1", "2", "3<", "5<"],
            ),
        ]:
            with self.subTest(codes=codes, query=query):
                defn1 = Definition.from_codes(codes, hierarchy)
                self.assertEqual(sorted(str(r) for r in defn1.rules), sorted(query))
                self.assertEqual(defn1.codes(hierarchy), codes)

                defn2 = Definition.from_query(query)
                self.assertEqual(sorted(str(r) for r in defn2.rules), sorted(query))
                self.assertEqual(defn2.codes(hierarchy), codes)

    @settings(deadline=None)
    @given(hierarchies(24), st.sets(st.sampled_from(range(16))), st.floats(0.1, 0.5))
    def test_roundtrip(self, hierarchy, codes, r):
        definition = Definition.from_codes(codes, hierarchy, r)
        self.assertEqual(definition.codes(hierarchy), codes)
        fragments = [rule.fragment for rule in definition.rules]
        self.assertEqual(len(fragments), len(set(fragments)))
        definition_codes = [rule.code for rule in definition.rules]
        self.assertEqual(len(definition_codes), len(set(definition_codes)))
