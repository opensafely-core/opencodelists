import json
from collections import defaultdict
from itertools import chain


class Hierarchy:
    """A directed acyclic graph with a single root.  This is used to represent a subset
    of the concepts in a coding system.
    """

    def __init__(self, root, edges):
        """Build a hierarchy with given root and collection of edges.  Edges are
        (parent, child) tuples.
        """

        self.root = root

        self.nodes = set()
        child_map = defaultdict(set)
        parent_map = defaultdict(set)

        for parent, child in edges:
            self.nodes.add(parent)
            self.nodes.add(child)
            child_map[parent].add(child)
            parent_map[child].add(parent)

        self.child_map = dict(child_map)
        self.parent_map = dict(parent_map)

        self._descendants_cache = {}
        self._ancestors_cache = {}

    def __eq__(self, other):
        """Compare hierarchies excluding cache items, resolving possible deserialisation differences"""

        def resolve_deser_nulls(_dict):
            return {k or "null": {i or "null" for i in v} for k, v in _dict.items()}

        return (
            self.root == other.root
            and self.nodes == other.nodes
            and resolve_deser_nulls(self.child_map)
            == resolve_deser_nulls(other.child_map)
            and resolve_deser_nulls(self.parent_map)
            == resolve_deser_nulls(other.parent_map)
        )

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

        # We add an edge from the root node to each code that does not appear in
        # ancestor_relationships or descendant_relationships (eg inactive SNOMED CT
        # concepts, or certain TPP Y-Codes).
        codes_in_edges = set(chain(*edges))
        for code in codes:
            if code not in codes_in_edges:
                edges.add((coding_system.root, code))

        return cls(coding_system.root, edges)

    @classmethod
    def from_cache(cls, data):
        instance = cls.__new__(cls)
        data = json.loads(data)
        instance.root = data["root"]
        instance.nodes = set(data["nodes"])
        instance.child_map = {
            parent: set(children) for parent, children in data["child_map"].items()
        }
        instance.parent_map = {
            child: set(parents) for child, parents in data["parent_map"].items()
        }
        instance._descendants_cache = {
            ancestor: set(descendants)
            for ancestor, descendants in data["_descendants_cache"].items()
        }
        instance._ancestors_cache = {
            descendant: set(ancestors)
            for descendant, ancestors in data["_ancestors_cache"].items()
        }
        instance.dirty = False
        return instance

    def data_for_cache(self):
        data = {
            "root": self.root,
            "nodes": list(self.nodes),
            "child_map": {
                parent: list(children) for parent, children in self.child_map.items()
            },
            "parent_map": {
                child: list(parents) for child, parents in self.parent_map.items()
            },
            "_descendants_cache": {
                ancestor: list(descendants)
                for ancestor, descendants in self._descendants_cache.items()
            },
            "_ancestors_cache": {
                descendant: list(ancestors)
                for descendant, ancestors in self._ancestors_cache.items()
            },
        }
        return json.dumps(data)

    def descendants(self, node):
        """Return set of descendants of node.

        A node's descendants are the node's children, plus all the children's
        descendants.
        """

        if node not in self._descendants_cache:
            descendants = set()
            for child in self.child_map.get(node, []):
                descendants.add(child)
                descendants |= self.descendants(child)
            self._descendants_cache[node] = descendants
            self.dirty = True

        return self._descendants_cache[node]

    def ancestors(self, node):
        """Return set of ancestors of node.

        A node's ancestors are the node's parents, plus all the parents' ancestors.
        """

        if node not in self._ancestors_cache:
            ancestors = set()
            for parent in self.parent_map.get(node, []):
                ancestors.add(parent)
                ancestors |= self.ancestors(parent)
            self._ancestors_cache[node] = ancestors
            self.dirty = True

        return self._ancestors_cache[node]

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
