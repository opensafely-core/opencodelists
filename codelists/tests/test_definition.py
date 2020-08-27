from unittest import TestCase

from hypothesis import given, settings
from hypothesis import strategies as st

from codelists.definition import Definition
from codelists.tree_utils import edges_to_paths, paths_to_tree


@st.composite
def dags(draw, size):
    """Construct a directed acyclic graph with `size` nodes.

    Returns dict mapping node to a set of its children.  Nodes are labelled 0
    to `size`-1, with 0 as the root.

    Based on an indea by @Zac-HD at https://github.com/HypothesisWorks/hypothesis/issues/2464.
    """

    node_to_children = {i: set() for i in range(size)}
    for child_id in range(1, size):
        for parent_id in draw(st.sets(st.sampled_from(range(child_id)), min_size=1)):
            node_to_children[parent_id].add(child_id)
    return node_to_children


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
        paths = edges_to_paths("0", edges)
        tree = paths_to_tree(paths)

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
                defn1 = Definition.from_codes(codes, tree)
                self.assertEqual(
                    sorted(str(rule) for rule in defn1.rules), sorted(query)
                )
                self.assertEqual(defn1.codes(tree), codes)

                defn2 = Definition.from_query(query)
                self.assertEqual(
                    sorted(str(rule) for rule in defn2.rules), sorted(query)
                )
                self.assertEqual(defn2.codes(tree), codes)

    @settings(deadline=None)
    @given(dags(24), st.sets(st.sampled_from(range(16))), st.floats(0.1, 0.5))
    def test_roundtrip(self, dag, codes, r):
        edges = [
            (parent, child) for parent, children in dag.items() for child in children
        ]
        paths = edges_to_paths(0, edges)
        tree = paths_to_tree(paths)
        definition = Definition.from_codes(codes, tree, r)
        self.assertEqual(definition.codes(tree), codes)
        fragments = [rule.fragment for rule in definition.rules]
        self.assertEqual(len(fragments), len(set(fragments)))
        definition_codes = [rule.code for rule in definition.rules]
        self.assertEqual(len(definition_codes), len(set(definition_codes)))
