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

    def __init__(self, code, excluded=False, includes_children=False):
        self.code = code
        self.excluded = excluded
        self.includes_children = includes_children

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

        return cls(fragment, excluded=excluded, includes_children=includes_children)


class Definition:
    """
    The Definition of a Codelist.

    A Codelist is defined as a set of Concepts, a subset of a Coding System.
    """

    def __init__(self, elements):
        self.elements = set(elements)

    def excluded_elements(self):
        for e in self.elements:
            if e.excluded:
                yield e

    def included_elements(self):
        for e in self.elements:
            if not e.excluded:
                yield e

    def codes(self, tree):
        """
        Get a Definition's Concept codes.

        Generate a set of codes for this Definition from it's
        DefinitionElements.
        """
        codes = set()
        descendants_map = tree_utils.build_descendants_map(tree)

        for e in self.included_elements():
            codes.add(e.code)
            if e.includes_children:
                codes |= descendants_map[e.code]

        for e in self.excluded_elements():
            try:
                codes.remove(e.code)
            except KeyError:
                print(e.code)
                pass
            if e.includes_children:
                codes -= descendants_map[e.code]

        return codes

    @classmethod
    def from_query(cls, fragments):
        elements = [DefinitionElement.from_fragment(f) for f in fragments]
        return cls(elements)

    @classmethod
    def from_codes(cls, codes, tree, r=0.25):
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
                if code in codes:
                    descendants = descendants_map[code]
                    descendants_not_in_codes = descendants - codes
                    if descendants:
                        ratio = len(descendants_not_in_codes) / len(descendants)
                    else:
                        ratio = 1

                    if ratio < r:
                        yield DefinitionElement(code, includes_children=True)
                        yield from negative_helper(tree[code])
                    else:
                        yield DefinitionElement(code)
                        yield from helper(tree[code])
                else:
                    yield from helper(tree[code])

        def negative_helper(tree):
            for code in sorted(tree):
                if code not in codes:
                    descendants = descendants_map[code]
                    if descendants and not descendants & codes:
                        yield DefinitionElement(
                            code, excluded=True, includes_children=True
                        )
                    else:
                        yield DefinitionElement(code, excluded=True)
                        yield from negative_helper(tree[code])
                else:
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

        return cls(elements)


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


def iter_definitions(elements, code_to_name, descendants_map, excluded=None):
    for element in elements:
        row = Row(
            name=code_to_name[element.code],
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
        row.excluded_children = list(
            iter_definitions(excluded_children, code_to_name, descendants_map)
        )

        yield attr.asdict(row)


def build_definition(coding_system, subtree, definition):
    code_to_name = coding_system.lookup_names([e.code for e in definition.elements])
    descendants_map = tree_utils.build_descendants_map(subtree)

    def sort_key(e):
        return code_to_name[e.code]

    elements = sorted(definition.included_elements(), key=sort_key)
    excluded = sorted(definition.excluded_elements(), key=sort_key)

    return list(iter_definitions(elements, code_to_name, descendants_map, excluded))
