from . import tree_utils


class DefinitionElement:
    def __init__(self, code, negated=False, includes_children=False):
        self.code = code
        self.negated = negated
        self.includes_children = includes_children

        self.fragment = str(self.code)
        if self.negated:
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
        if fragment[0] == "~":
            negated = True
            fragment = fragment[1:]
        else:
            negated = False

        if fragment[-1] == "<":
            includes_children = True
            fragment = fragment[:-1]
        else:
            includes_children = False

        return cls(fragment, negated=negated, includes_children=includes_children)


class Definition:
    def __init__(self, elements):
        self.elements = set(elements)

    def negated_elements(self):
        for e in self.elements:
            if e.negated:
                yield e

    def unnegated_elements(self):
        for e in self.elements:
            if not e.negated:
                yield e

    def codes(self, tree):
        codes = set()
        descendants_map = tree_utils.build_descendants_map(tree)

        for e in self.unnegated_elements():
            codes.add(e.code)
            if e.includes_children:
                codes |= descendants_map[e.code]

        for e in self.negated_elements():
            codes.remove(e.code)
            if e.includes_children:
                codes -= descendants_map[e.code]

        return codes

    @classmethod
    def from_query(cls, fragments):
        elements = [DefinitionElement.from_fragment(f) for f in fragments]
        return cls(elements)

    @classmethod
    def from_codes(cls, codes, tree, r=0.25):
        codes = set(codes)
        descendants_map = tree_utils.build_descendants_map(tree)

        def helper(tree):
            for code in tree:
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
            for code in tree:
                if code not in codes:
                    descendants = descendants_map[code]
                    if descendants and not descendants & codes:
                        yield DefinitionElement(
                            code, negated=True, includes_children=True
                        )
                    else:
                        yield DefinitionElement(code, negated=True)
                        yield from negative_helper(tree[code])
                else:
                    yield from negative_helper(tree[code])

        return cls(list(helper(tree)))
