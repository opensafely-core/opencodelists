from collections import defaultdict
from functools import lru_cache
from itertools import chain

from django.utils.functional import cached_property


class Hierarchy:
    """A directed acyclic graph with a single root.  This is used to represent a subset
    of the concepts in a coding system.
    """

    def __init__(self, root, edges):
        """Build a hierarchy with given root and collection of edges.  Edges are
        (parent, child) tuples.
        """

        self.root = root
        self.edges = edges

    @classmethod
    def from_codes(cls, coding_system, codes):
        """Build a hierarchy containing the given codes, and their ancestors/descendants
        in the coding system.
        """

        if isinstance(codes, str):
            msg = "Hierarchy was expecting codes to be a non-string iterable, you passed a string."
            raise TypeError(msg)

        ancestor_relationships = set(coding_system.ancestor_relationships(codes))
        descendant_relationships = set(coding_system.descendant_relationships(codes))
        edges = ancestor_relationships | descendant_relationships
        return cls(coding_system.root, edges)

    @cached_property
    def nodes(self):
        """Set of nodes in graph."""
        return set(chain.from_iterable(self.edges))

    @cached_property
    def child_map(self):
        """Dict mapping each node to the set of its immediate children."""

        m = defaultdict(set)
        for parent, child in self.edges:
            m[parent].add(child)
        return dict(m)

    @cached_property
    def parent_map(self):
        """Dict mapping each node to the set of its immediate parents."""

        m = defaultdict(set)
        for parent, child in self.edges:
            m[child].add(parent)
        return dict(m)

    @lru_cache(maxsize=None)
    def descendants(self, node):
        """Return set of descendants of node.

        A node's descendants are the node's children, plus all the children's
        descendants.
        """

        descendants = set()
        for child in self.child_map.get(node, []):
            descendants.add(child)
            descendants |= self.descendants(child)
        return descendants

    @lru_cache(maxsize=None)
    def ancestors(self, node):
        """Return set of ancestors of node.

        A node's ancestors are the node's parents, plus all the parents' ancestors.
        """

        ancestors = set()
        for parent in self.parent_map.get(node, []):
            ancestors.add(parent)
            ancestors |= self.ancestors(parent)
        return ancestors

    def filter_to_ultimate_ancestors(self, nodes):
        """Given a set of nodes, return subset which have no ancestors in the set."""

        return {node for node in nodes if not self.ancestors(node) & nodes}

    def node_status(self, node, included, excluded):
        r"""Return status of node.  See the docstring for Codeset for possible status
        values.

        For example, for this graph:

               a
              / \
             b   c
            / \ / \
           d   e   f
          / \ / \ / \
         g   h   i   j

        with a and e included, and b and c excluded, nodes will have the statues according
        to this diagram:

               +
              / \
             -   -
            / \ / \
          (-)  +  (-)
          / \ / \ / \
        (-) (+) (+) (-)

        So graph.node_to_status({"a", "e"}, {"b", "c"}) returns

        {
            "a": "+",
            "b": "-",
            "c": "-",
            "d": "(-)",
            "e": "+",
            "f": "(-)",
            "g": "(-)",
            "h": "(+)",
            "i": "(+)",
            "j": "(-)",
        }

        See test_node_to_status for more examples.
        """
        if node in included:
            # this node is explicitly included
            return "+"
        if node in excluded:
            # this node is explicitly excluded
            return "-"

        # these are the ancestors of the node
        ancestors = self.ancestors(node)

        # these are the ancestors of the node that are directly included or excluded
        included_or_excluded_ancestors = ancestors & (included | excluded)

        if not included_or_excluded_ancestors:
            # no ancestors are included or excluded, so this node is neither excluded or
            # excluded
            return "?"

        # these are the ancestors of the node that are directly included or excluded,
        # and which are not overridden by any of their descendants
        significant_included_or_excluded_ancestors = {
            a
            for a in included_or_excluded_ancestors
            if not (included_or_excluded_ancestors & self.descendants(a))
        }

        # these are the significant included ancestors of the node
        included_ancestors = significant_included_or_excluded_ancestors & included

        # these are the significant excluded ancestors of the node
        excluded_ancestors = significant_included_or_excluded_ancestors & excluded

        if included_ancestors and not excluded_ancestors:
            # some ancestors are included and none are excluded, so this node is
            # included
            return "(+)"
        if excluded_ancestors and not included_ancestors:
            # some ancestors are excluded and none are included, so this node is
            # excluded
            return "(-)"

        # some ancestors are included and some are excluded, and neither set of
        # ancestors overrides the other
        return "!"
