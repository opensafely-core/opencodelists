import attr


@attr.s
class DummyCodingSystem:
    """
    A dummy Coding System

    When testing some areas we need to create a fake Coding System.  This class
    mirrors the Coding System API while not talking to the database.
    """

    name: str = attr.ib()
    short_name: str = attr.ib()
    root: str = attr.ib()
    edges: list = attr.ib()
    tree: dict = attr.ib()

    def ancestor_relationships(self, codes):
        """
        Build ancestor edges based on the requested codes

        This method is used to walk up a Coding Systems graph from the given
        starting points (codes) to find edges (tuples of parent, child) with a
        common ancestor to the chosen codes.
        """
        # ancestor_relationships
        # list of tuples where 0 is child of 1

        # Given:
        #
        #      ┌--0--┐
        #      |     |
        #   ┌--1--┌--2--┐
        #   |     |     |
        # ┌-3-┐ ┌-4-┐ ┌-5-┐
        # |   | |   | |   |
        # 6   7 8   9 10 11

        # Expected:
        #
        # +-----------+-----------+
        # | parent_id | child_id |
        # +-----------+----------+
        # | 0         | 1        |
        # | 0         | 2        |
        # | 1         | 3        |
        # | 1         | 4        |
        # | 2         | 4        |
        # | 2         | 5        |
        # | 3         | 6        |
        # | 3         | 7        |
        # | 4         | 8        |
        # | 4         | 9        |
        # | 5         | 10       |
        # | 5         | 11       |
        # +-----------+-----------+

        # From 128133004< (tennis elbow) (12 rows)
        # +-----------+-----------+
        # | parent_id | child_id  |
        # +-----------+-----------+
        # | 118947000 | 128133004 |
        # | 116309007 | 128133004 |
        # | 128605003 | 118947000 |
        # | 116307009 | 118947000 |
        # | 116307009 | 116309007 |
        # | 123946008 | 128605003 |
        # | 302293008 | 128605003 |
        # | 302293008 | 116307009 |
        # | 64572001  | 123946008 |
        # | 118234003 | 123946008 |
        # | 301857004 | 302293008 |
        # | 404684003 | 64572001  |
        # | 404684003 | 118234003 |
        # | 118234003 | 301857004 |
        # | 138875005 | 404684003 |
        # +-----------+-----------+

        def iter_edges(edges, codes):
            # for each code find edges where they are the child
            for parent, child in edges:
                if child in codes:
                    yield (parent, child)

        def iter_parents(edges):
            parents = {parent for parent, _ in edges}
            children = {child for _, child in edges}

            yield from parents - children

        # given some codes
        # get the edges where those codes are the direct parents
        relations = set(iter_edges(self.edges, codes))

        # find all the parents which aren't already children in the edges
        parents = list(iter_parents(relations))
        print(parents)

        # # if there is more than one parent
        # if len(parents) > 1:
        #     relations |= set(iter_edges(self.edges, parents))
        #     parents = list(iter_parents(relations))
        #  swap those for codes

        while len(parents) > 1:
            new_relations = set(iter_edges(self.edges, parents))
            parents = list(iter_parents(new_relations))
            relations |= new_relations

        print(parents)
        print(sorted(relations))

        return list(sorted(relations))

        # parents = []
        # relations = list(iter_edges(self.edges, codes))

        # import ipdb

        # ipdb.set_trace()

        # while len(parents) != 1:
        #     print(f"parents: ({len(parents)}) {parents}")

        #     new = list(iter_edges(self.edges, parents))

        #     # get parents from current relations
        #     # if there is more than one parent, find their parents
        #     parents = [parent for parent, child in new]

        #     relations.extend(new)

        # return relations
        # for parent, child in self.edges:
        #     if child in codes:
        #         yield (parent, child)

        # return [a for a in self.ancestors if a[0] in codes]

    def descendant_relationships(self, codes):
        relations = set()
        # find all edges where the parent is in codes
        # for parent, child in self.edges:
        #     if parent in codes:
        #         relations.add((parent, child))

        def iter_edges(edges, codes):
            for parent, child in edges:
                if parent in codes:
                    yield (parent, child)

        # direct edges from given codes
        updates = set(iter_edges(self.edges, codes))

        while updates:
            relations |= updates

            # get all the children from that set
            children = {child for _, child in updates}

            updates = set(iter_edges(self.edges, children))

        return list(sorted(relations))
        # return [d for d in self.descendants if d[0] in codes]


def iter_ancestor_relationships(tree):
    for parent, children in tree.items():
        for child in children.keys():
            print(parent, child)
            # yield from helper(children)

    # for parent, children in ancestors.items():
    #     for child in children:
    #         yield (child, parent)


def iter_descendant_relationships(tree):
    # descendant_relationships = attr.ib()
    # list of tuples where 0 is parent of 1

    # Given:
    #
    #      ┌--0--┐
    #      |     |
    #   ┌--1--┌--2--┐
    #   |     |     |
    # ┌-3-┐ ┌-4-┐ ┌-5-┐
    # |   | |   | |   |
    # 6   7 8   9 10 11

    # Expected:
    #
    # +-----------+-----------+
    # | parent_id | child_id |
    # +-----------+----------+
    # | 0         | 1        |
    # | 0         | 2        |
    # | 1         | 3        |
    # | 1         | 4        |
    # | 2         | 4        |
    # | 2         | 5        |
    # | 3         | 6        |
    # | 3         | 7        |
    # | 4         | 8        |
    # | 4         | 9        |
    # | 5         | 10       |
    # | 5         | 11       |
    # +-----------+-----------+

    # From 128133004< (tennis elbow) (7 rows)
    # +-----------+-----------+
    # | parent_id | child_id  |
    # +-----------+-----------+
    # | 128133004 | 239964003 |
    # | 128133004 | 35185008  |
    # | 128133004 | 429554009 |
    # | 35185008  | 73583000  |
    # | 429554009 | 439656005 |
    # | 73583000  | 202855006 |
    # | 439656005 | 202855006 |
    # +-----------+-----------+

    def helper(t):
        for parent, children in t.items():
            for child in children.keys():
                yield (parent, child)
                yield from helper(children)

    yield from helper(tree)


def build_dummy_coding_system(*, name="dummy", short_name="dummy", edges, tree):
    if len(tree.keys()) > 1:
        raise Exception("Tree should only have one root node")

    root = list(tree.keys())[0]
    print(tree)

    # ancestor_relationships = list(iter_ancestor_relationships(tree))
    # print(ancestor_relationships)
    # descendant_relationships = list(iter_descendant_relationships(tree))
    # print(descendant_relationships)

    return DummyCodingSystem(
        name=name, short_name=short_name, root=root, edges=edges, tree=tree
    )
