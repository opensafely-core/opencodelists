# Concepts in a coding system are arranged in a hierarchy.
#
# We have to deal with lists of concepts, from either:
#
#  * a codelist
#  * a term search
#
# Given a collection of concepts, we want to know:
#
#  * which concepts are ancestors/descendants of a particular concept
#  * which concepts in the collection have no ancestors in the collection
#  * how the concepts can be arranged in a tree
#
# We can represent a coding system hierarchy as a directed acyclic graph (a DAG), where
# the nodes are labeled by concept codes, and the directed edges are parent/child
# relationships between concepts.
#
# We can make our lives more manageable by filtering a coding system hierarchy to
# produce a DAG that only has nodes that are directly related to the codes in the
# collection of concepts we're currently interested in.
#
# A coding system can provide a collection of parent/child relationships.  We can
# represent a DAG as one or both of:
#
#  * parent_map: a dict mapping each node to the set of its immediate parents
#  * child_map: a dict mapping each node to the set of its immediate children

import itertools
from django.utils.functional import cached_property


class DAG:
    def __init__(self, *, root, edges):
        self.root = root
        self.edges = edges

    @cached_property
    def nodes(self):
        """Set of nodes in graph.
        """
        return set(itertools.chain.from_iterable(self.edges))

    @cached_property
    def parent_map(self):
        """Dict mapping each node to the set of its immediate parents.
        """

        m = {node: set() for node in self.nodes}
        for parent, child in self.edges:
            m[child].add(parent)
        return m

    @cached_property
    def child_map(self):
        """Dict mapping each node to the set of its immediate children.
        """

        m = {node: set() for node in self.nodes}
        for parent, child in self.edges:
            m[parent].add(child)
        return m

    def ancestors(self, node):
        r"""Return set of ancestors of node.

        Starting at given node, work towards root, visiting parents of nodes.  Any new
        parents are added both to the set of ancestors, and the set of nodes to look at
        next.

        With:

            a
           / \
          b   c
         / \ / \
        d   e   f

        When working out ancestors of e, this table shows the values of node, todo, and
        ancestors, at points X and Y in the code below.

        node | todo (X) | ancestors (X) | todo (Y) | ancestors (Y)
        -----+----------+---------------+----------+--------------
        e    |  {}      | {}            | {b, c}   | {b, c}
        b    |  {c}     | {b, c}        | {a, c}   | {a, b, c}
        a    |  {c}     | {a, b, c}     | {c}      | {a, b, c}
        c    |  {}      | {a, b, c}     | {}       | {a, b, c}
        """

        todo = {node}
        ancestors = set()

        while todo:
            node = todo.pop()
            # point X
            parents = self.parent_map[node]
            new_ancestors = parents - ancestors
            todo |= new_ancestors
            ancestors |= new_ancestors
            # point Y

        return ancestors

    def descendants(self, node):
        r"""Return set of descendants of node.

        Starting at given node, work towards root, visiting parents of nodes.  Any new
        parents are added both to the set of ancestors, and the set of nodes to look at
        next.

        With:

            a
           / \
          b   c
         / \ / \
        d   e   f

        When working out descendants of a, this table shows the values of node, todo, and
        descendants, at points X and Y in the code below.

        node | todo (X) | descendants (X) | todo (Y) | descendants (Y)
        -----+----------+-----------------+----------+----------------
        a    |  {}      | {}              | {b, c}   | {b, c}
        b    |  {c}     | {b, c}          | {c, d, e}| {b, c, d, e}
        d    |  {c, e}  | {b, c, d, e}    | {c, e}   | {b, c, d, e}
        c    |  {e}     | {b, c, d, e}    | {e, f}   | {b, c, d, e, f}
        f    |  {e}     | {b, c, d, e}    | {e}      | {b, c, d, e, f}
        e    |  {}      | {b, c, d, e}    | {}       | {b, c, d, e, f}
        """

        todo = {node}
        descendants = set()

        while todo:
            node = todo.pop()
            # point X
            children = self.child_map[node]
            new_descendants = children - descendants
            todo |= new_descendants
            descendants |= new_descendants
            # point Y

        return descendants
