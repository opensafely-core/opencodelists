from collections import defaultdict, namedtuple
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

        ancestor_relationships = set(coding_system.ancestor_relationships(codes))
        descendant_relationships = set(coding_system.descendant_relationships(codes))
        edges = ancestor_relationships | descendant_relationships
        return cls(coding_system.root, edges)

    @cached_property
    def nodes(self):
        """Set of nodes in graph.
        """
        return set(chain.from_iterable(self.edges))

    @cached_property
    def child_map(self):
        """Dict mapping each node to the set of its immediate children.
        """

        m = defaultdict(set)
        for parent, child in self.edges:
            m[parent].add(child)
        return m

    @cached_property
    def parent_map(self):
        """Dict mapping each node to the set of its immediate parents.
        """

        m = defaultdict(set)
        for parent, child in self.edges:
            m[child].add(parent)
        return m

    @lru_cache(maxsize=None)
    def descendants(self, node):
        """Return set of descendants of node.

        A node's descendants are the node's children, plus all the children's
        descendants.
        """

        descendants = set()
        for child in self.child_map[node]:
            descendants.add(child)
            descendants |= self.descendants(child)
        return descendants

    @lru_cache(maxsize=None)
    def ancestors(self, node):
        """Return set of ancestors of node.

        A node's ancestors are the node's parents, plus all the parents' ancestors.
        """

        ancestors = set()
        for parent in self.parent_map[node]:
            ancestors.add(parent)
            ancestors |= self.ancestors(parent)
        return ancestors

    def walk_depth_first_as_tree(self, starting_node=None, sort_key=None):
        """Walk graph depth-first from root, yielding NodeWithMetadata tuples on
        entering and exiting each node.  Each node may be visited more than once if
        there is more than one path to the node from the starting node.

        See tests for an example.
        """

        def helper(node, depth):
            children = self.child_map[node]
            size = len(children)
            for ix, child in enumerate(sorted(children, key=sort_key)):
                yield NodeWithMetadata(
                    label=child,
                    depth=depth,
                    left_ix=ix,
                    right_ix=(size - 1) - ix,
                    direction=1,
                )
                yield from (helper(child, depth + 1))
                yield NodeWithMetadata(
                    label=child,
                    depth=depth,
                    left_ix=ix,
                    right_ix=(size - 1) - ix,
                    direction=-1,
                )

        if starting_node is None:
            starting_node = self.root

        yield NodeWithMetadata(
            label=starting_node, depth=0, left_ix=0, right_ix=0, direction=1
        )
        yield from helper(starting_node, 1)
        yield NodeWithMetadata(
            label=starting_node, depth=0, left_ix=0, right_ix=0, direction=-1
        )

    def filter_to_ultimate_ancestors(self, nodes):
        """Given a set of nodes, return subset which have no ancestors in the set.
        """

        return {node for node in nodes if not self.ancestors(node) & nodes}

    def update_node_to_status(self, node_to_status, updates):
        """Given a mapping from each node to its status and a list of updates, return an
        updated mapping.

        Each status is one of:

        * +   included directly
        * -   excluded directly
        * (+) included indirectly by one or more ancestors
        * (-) excluded indirectly by one or more ancestors
        * ?   neither included nor excluded
        * !   in conflict: has some ancestors which are directly included and some which are
                directly excluded, and neither set overrides the other

        Updates are tuples of (node, new_status), where new_status is one of:

        * +   include this node, and all descendants that are not otherwise excluded
        * -   exclude this node, and all descendants that are not otherwise included
        * ?   clear this node's status, and do so for all descendants that are not otherwise
                included or excluded
        """

        included = {node for node, status in node_to_status.items() if status == "+"}
        excluded = {node for node, status in node_to_status.items() if status == "-"}

        assert included & excluded == set()

        for node, status in updates:
            if node in included:
                included.remove(node)
            if node in excluded:
                excluded.remove(node)

            if status == "+":
                included.add(node)
            if status == "-":
                excluded.add(node)

        assert included & excluded == set()

        nodes_to_update = set()
        for node, status in updates:
            nodes_to_update.add(node)
            nodes_to_update |= self.descendants(node)

        return {
            node: self.node_status(node, included, excluded) for node in nodes_to_update
        }

    def node_status(self, node, included, excluded):
        r"""Return status of node.  See the docstring for update_node_to_status() for
        possible status values.

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


# Represents visiting a node in a hierarchy.
NodeWithMetadata = namedtuple(
    "NodeWithMetadata",
    [
        "label",  # the node's label
        "depth",  # the length of the shorted path from the root to the node
        "left_ix",  # the index of the node in the sorted list of its siblings
        "right_ix",  # the right-index of the node in the sorted list of its siblings
        "direction",  # 1 when entering a node; -1 when exiting it
    ],
)
