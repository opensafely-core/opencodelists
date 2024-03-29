from collections import deque
from io import BytesIO
from itertools import chain

from hypothesis import strategies as st

from codelists.hierarchy import Hierarchy
from coding_systems.base.coding_system_base import DummyCodingSystem


def csv_builder(contents):
    """
    Build a CSV from the given contents

    When testing CSVs in views and forms we need to replicate an uploaded CSV,
    this does that with the use of BytesIO.
    """
    buffer = BytesIO()
    buffer.write(contents.encode("utf8"))
    buffer.seek(0)
    return buffer


def build_small_hierarchy():
    r"""Return hierarchy with this structure:

        a
       / \
      b   c
     / \ / \
    d   e   f
    """

    edges = [
        ("a", "b"),
        ("a", "c"),
        ("b", "d"),
        ("b", "e"),
        ("c", "e"),
        ("c", "f"),
    ]

    return Hierarchy("a", edges)


def build_hierarchy():
    r"""Return hierarchy with this structure:

           a
          / \
         b   c
        / \ / \
       d   e   f
      / \ / \ / \
     g   h   i   j
    """

    edges = [
        ("a", "b"),
        ("a", "c"),
        ("b", "d"),
        ("b", "e"),
        ("c", "e"),
        ("c", "f"),
        ("d", "g"),
        ("d", "h"),
        ("e", "h"),
        ("e", "i"),
        ("f", "i"),
        ("f", "j"),
    ]

    return Hierarchy("a", edges)


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


class MockCodingSystem(DummyCodingSystem):
    r"""
    Model a mock coding system as a Hierarchy, which consists of
    a set of nodes with relationships between nodes represented by a dict of
    parents to chilren and children to parents.

    Ancenstor and descendant relationships are built by walking up and down the
    parent and child maps

    e.g. assume a coding system with the structure generated by the `build_hierarchy`
    function above.

    We pass in build_hierarchy(), to generate a coding system that looks like this:

           a
          / \
         b   c
        / \ / \
       d   e   f
      / \ / \ / \
     g   h   i   j

    Tests can then use this mock coding system to build hierarchies from subsets of codes.

    coding_system = MockCodingSystem(hierarchy=build_hierarchy())
    hierarchy = Hierarchy.from_codes(coding_system, ["d"])
    This generates a new hierarchy that looks like this:
           a
          /
         b
        / \
       d   e
      / \ / \
     g   h   i
    """

    id = "mock"
    name = "mock coding system"
    short_name = "mock"

    def __init__(self, hierarchy, database_alias="mock_db"):
        super().__init__(database_alias=database_alias)
        self.root = hierarchy.root
        self.hierarchy = hierarchy

    def ancestor_relationships(self, codes):
        """
        Walk up the parent_map from each code and find all (parent, child) edges
        """
        return set(chain(*[self.walk_tree(code, "up") for code in codes]))

    def descendant_relationships(self, codes):
        """
        Walk down the child_map from each code and find all (parent, child) edges
        """
        return set(chain(*[self.walk_tree(code, "down") for code in codes]))

    def walk_tree(self, code, direction):
        "returns a list of (parent, child) tuples"
        edge_list = []
        to_walk = deque([code])
        if direction == "down":
            tree = self.hierarchy.child_map
        else:
            tree = self.hierarchy.parent_map

        while to_walk:
            current = to_walk.popleft()
            node_children = tree.get(current, [])
            to_walk.extend(node_children)
            for child in node_children:
                if direction == "down":
                    # walking down the tree, current is the parent
                    edge_list.append((current, child))
                else:
                    # walking up the tree, current is the child
                    edge_list.append((child, current))
        return edge_list
