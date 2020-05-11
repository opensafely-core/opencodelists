from unittest import TestCase

import hypothesis.strategies as st
from hypothesis import given

from codelists.definition import Definition

from .helpers import build_tree


class DefinitionTests(TestCase):
    def test_roundtrip_examples(self):
        tree = build_tree(4)

        # tree has this structure:
        #
        #      ┌-----1-----┐
        #      |           |
        #   ┌--2--┐     ┌--3--┐
        #   |     |     |     |
        # ┌-4-┐ ┌-5-┐ ┌-6-┐ ┌-7-┐
        # |   | |   | |   | |   |
        # 8   9 10 11 12 13 14 15

        for codes, query in [
            # the root element
            ({"1"}, ["1"]),
            # an intermediate element
            ({"2"}, ["2"]),
            # the leaf element
            ({"8"}, ["8"]),
            # everything under intermediate element, inclusive
            ({"2", "4", "5", "8", "9", "10", "11"}, ["2<"]),
            # everything under intermediate element, exclusive
            ({"4", "5", "8", "9", "10", "11"}, ["4<", "5<"]),
            # everything under intermediate element, except another intermediate element
            ({"2", "5", "8", "9", "10", "11"}, ["2<", "~4"]),
            # everything under intermediate element, except leaf element
            ({"2", "4", "5", "9", "10", "11"}, ["2<", "~8"]),
            # everything under root element, except intermediate element and its children
            (
                {"1", "2", "3", "5", "6", "7", "10", "11", "12", "13", "14", "15"},
                ["1<", "~4<"],
            ),
        ]:
            with self.subTest(codes=codes, query=query):
                defn1 = Definition.from_codes(codes, tree)
                self.assertEqual(sorted(str(e) for e in defn1.elements), sorted(query))
                self.assertEqual(defn1.codes(tree), codes)

                defn2 = Definition.from_query(query)
                self.assertEqual(sorted(str(e) for e in defn2.elements), sorted(query))
                self.assertEqual(defn2.codes(tree), codes)

    @given(st.data())
    def test_roundtrip(self, data):
        tree_depth = 5
        codes = {
            str(code) for code in range(1, 2 ** tree_depth) if data.draw(st.booleans())
        }
        r = data.draw(st.floats(0.1, 0.5))

        tree = build_tree(tree_depth)
        definition = Definition.from_codes(codes, tree, r)
        self.assertEqual(definition.codes(tree), codes)
        fragments = [e.fragment for e in definition.elements]
        self.assertEqual(len(fragments), len(set(fragments)))
