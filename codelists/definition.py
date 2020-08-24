import attr

from . import tree_utils


class DefinitionElement:
    """
    An element in a Definition ~= a Concept.

    DefinitionElements represent a Concept in a Coding System with some extra
    information to help in building a representation of a Definition.

    It knows:
     * if it's excluded from the encapsulation Definition
     * if it's children are included in the Definition
     * how to express the above two and it's code as a query string
    """

    def __init__(self, code, name, excluded=False, includes_children=False):
        self.code = code
        self.name = name
        self.excluded = excluded
        self.includes_children = includes_children

        # missing: should be shown?
        # missing:

        self.fragment = str(self.code)
        if self.excluded:
            self.fragment = "~" + self.fragment
        if self.includes_children:
            self.fragment = self.fragment + "<"

    def __str__(self):
        return self.fragment

    def __repr__(self):
        return f"[DefinitionElement {self.fragment}]"

    def __eq__(self, other):
        return type(self) == type(other) and self.fragment == other.fragment

    def __hash__(self):
        return hash(self.fragment)

    @classmethod
    def from_fragment(cls, fragment):
        """
        Generate a DefinitionElement from the given fragment.

        Since a fragment is a string representation of a DefinitionElement we
        can deserialize a fragment string back into a DefinitionElement.
        """
        if fragment[0] == "~":
            excluded = True
            fragment = fragment[1:]
        else:
            excluded = False

        if fragment[-1] == "<":
            includes_children = True
            fragment = fragment[:-1]
        else:
            includes_children = False

        print(f"Generating DefinitionElement from: {fragment}")
        return cls(
            fragment, name="", excluded=excluded, includes_children=includes_children
        )


class Definition:
    """
    The Definition of a Codelist.

    A Codelist is defined as a set of Concepts, a subset of a Coding System.
    """

    def __init__(self, tree, elements, descendants_map):
        self.tree = tree
        self.elements = set(elements)
        self.descendants_map = descendants_map

    def excluded_elements(self):
        for e in self.elements:
            if e.excluded:
                yield e

    def included_elements(self):
        for e in self.elements:
            if not e.excluded:
                yield e

    @classmethod
    def from_query(cls, fragments):
        elements = [DefinitionElement.from_fragment(f) for f in fragments]
        print(f"Created {len(elements)} elements")
        return cls(elements)

    @classmethod
    def from_codes(cls, code_to_name, codes, tree, r=0.25):
        """
        Generate a Definition from the given codes.

        The given tree is a subtree (slice/subset) of the Coding System graph.

        We traverse the tree of Concepts to create DefinitionElements. However,
        the tree is a superset of the given codes because it maintains
        relations between Concepts so we have to decide which Concepts are
        included or excluded.  This is where the the given r comes in.  We need
        a way to define when we include an excluded Concept (eg because it's
        children are included) or ignore it.

        TODO: is this last bit correct?
        """
        codes = set(codes)
        descendants_map = tree_utils.build_descendants_map(tree)

        def helper(tree):
            for code in sorted(tree):
                if code not in codes:
                    yield from helper(tree[code])
                    continue

                name = code_to_name[code]
                descendants = descendants_map[code]
                descendants_not_in_codes = descendants - codes
                if descendants:
                    ratio = len(descendants_not_in_codes) / len(descendants)
                else:
                    ratio = 1

                if ratio < r:
                    yield DefinitionElement(code, name, includes_children=True)
                    yield from negative_helper(tree[code])
                else:
                    yield DefinitionElement(code, name)
                    yield from helper(tree[code])

        def negative_helper(tree):
            for code in sorted(tree):
                if code in codes:
                    yield from negative_helper(tree[code])
                    continue

                name = code_to_name[code]
                descendants = descendants_map[code]
                if descendants and not descendants & codes:
                    yield DefinitionElement(
                        code, name, excluded=True, includes_children=True
                    )
                else:
                    yield DefinitionElement(code, name, excluded=True)
                    yield from negative_helper(tree[code])

        elements = list(helper(tree))

        # Remove any elements that are included unnecessarily.
        #
        # For instance, in a polyhierarchy that includes:
        #
        #      \ /
        #       1
        #      / \
        #     2   3
        #      \ /
        #       4
        #      / \
        #
        # where all descendants of 1 are included except 2, we can end up with
        # the definition including 1< and 3<.  We can remove the 3<.

        excluded_codes = {e.code for e in elements if not e.excluded}
        for e in elements:
            if e.includes_children:
                excluded_codes -= descendants_map[e.code]
        elements = [e for e in elements if e.excluded or e.code in excluded_codes]

        return cls(tree, elements, descendants_map)

    @classmethod
    def from_dag(cls, dag):
        pass


def build_codes(included_elements, excluded_elements, tree):
    """Build a set of codes based on the given included/excluded DefinitionElements"""
    codes = set()
    descendants_map = tree_utils.build_descendants_map(tree)

    for e in included_elements:
        codes.add(e.code)
        if e.includes_children:
            codes |= descendants_map[e.code]

    for e in excluded_elements:
        try:
            codes.remove(e.code)
        except KeyError:
            print(e.code)
            pass
        if e.includes_children:
            codes -= descendants_map[e.code]

    return codes


def codes_from_query(coding_system, fragments):
    elements = [DefinitionElement.from_fragment(f) for f in fragments]

    included_elements = [e for e in elements if not e.excluded]
    excluded_elements = [e for e in elements if e.excluded]

    subtree = tree_utils.build_subtree(coding_system, [e.code for e in elements])
    print(subtree)

    return build_codes(included_elements, excluded_elements, subtree)


@attr.s
class Row:
    """
    Data structure for a Definition to prepare for display

    name: name of the definition
    code: code of the definition
    excluded_children: list of excluded children (created with this class too)
    all_descendants: are all of this Definitions descendants included?

    Between all_descendants and excluded_children we can cover the three state
    situation a Definition can be in:

        * all descendants are included (all_descendants = True, excluded_children = [])
        * all descendants except N (all_descendants = True, excluded_children = [...])
        * no descendants (all_descendants = False, excluded_children ignored)

    """

    name: str = attr.ib()
    code: str = attr.ib()
    excluded_children: list = attr.ib(default=list())
    all_descendants: bool = attr.ib(default=True)


def iter_rows(elements, descendants_map, excluded=None):
    for element in elements:
        row = Row(
            name=element.name,
            code=element.code,
            all_descendants=element.includes_children,
        )

        # no descendents for this code so we can shortcut the iteration here
        if not element.includes_children:
            yield attr.asdict(row)
            continue

        # get child Definitions for this element
        excluded_children = [
            e for e in excluded if e.code in descendants_map[element.code]
        ]

        # generate excluded children
        row.excluded_children = list(iter_rows(excluded_children, descendants_map))

        yield attr.asdict(row)


def build_rows(subtree, definition):
    descendants_map = tree_utils.build_descendants_map(subtree)

    elements = sorted(definition.included_elements(), key=lambda e: e.name)
    excluded = sorted(definition.excluded_elements(), key=lambda e: e.name)
    return list(iter_rows(elements, descendants_map, excluded))
