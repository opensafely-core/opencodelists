import attr


class Definition:
    """Represents a set of rules that define a list of codes.  Each rule indicates
    whether a given code is included (an "including rule") or excluded (an "excluding
    rule") in a list of codes, and whether the inclusion/exclusion applies to the code's
    descendants too.
    """

    def __init__(self, rules):
        self.rules = set(rules)

    def excluding_rules(self):
        """Yield rules that exclude a code (and possibly that code's descendants).
        """

        for rule in self.rules:
            if rule.code_is_excluded:
                yield rule

    def including_rules(self):
        """Yield rules that include a code (and possibly that code's descendants).
        """

        for rule in self.rules:
            if not rule.code_is_excluded:
                yield rule

    def codes(self, hierarchy):
        """Return set of codes that is defined by the rules.
        """

        codes = set()

        for rule in self.including_rules():
            codes.add(rule.code)

            if rule.applies_to_descendants:
                codes |= hierarchy.descendants(rule.code)

        for rule in self.excluding_rules():
            try:
                codes.remove(rule.code)
            except KeyError:
                # Sometimes a code can be excluded by more than one rule.
                pass

            if rule.applies_to_descendants:
                codes -= hierarchy.descendants(rule.code)

        return codes

    @classmethod
    def from_query(cls, fragments):
        """Build definition from list of string fragments.

        See DefinitionRule.from_fragment for expected format of each fragment.
        """

        rules = [DefinitionRule.from_fragment(f) for f in fragments]
        return cls(rules)

    @classmethod
    def from_codes(cls, codes, hierarchy, r=0.25):
        """Build definition from set of codes.

        We add a DefinitionRule for each code that is an ultimate ancestor of other
        codes in the set.

        For each code that is an ultimate ancester:

        * If the node has no descendants,  we add a DefinitionRule that applies only to
        the code.

        * If all the node's descendants are included in the set, we add a DefinitionRule
        that applies to that code and all its descendants.

        * If the proporition of a code's descendants that are missing from the
        set of codes is less than r, we add a DefinitionRule that applies to that code
        and all its descendants, and add extra rules that exclude the descendants that
        are missing.

        * Otherwise, we add a DefinitionRule for that code that does not apply to its
        descendants.  We then add further rules, by constructing a temporary definition
        for just the descendants of this code.
        """

        rules = []

        for ancestor in hierarchy.filter_to_ultimate_ancestors(codes):
            descendants = hierarchy.descendants(ancestor)

            if len(descendants) == 0:
                # This node has no descendants.
                rules.append(DefinitionRule(ancestor))
                continue

            descendants_not_in_codes = descendants - codes

            if len(descendants_not_in_codes) == 0:
                # All of this node's descendants are included.
                rules.append(DefinitionRule(ancestor, applies_to_descendants=True))
                continue

            ratio = len(descendants_not_in_codes) / len(descendants)

            if ratio < r:
                # Most of this node's descendants are included...
                rules.append(DefinitionRule(ancestor, applies_to_descendants=True))
                for descendant in descendants_not_in_codes:
                    # ...but a handful are excluded.
                    rules.append(DefinitionRule(descendant, code_is_excluded=True))
                continue

            # Only some of this node's descendants are included.
            rules.append(DefinitionRule(ancestor))
            sub_definition = Definition.from_codes(descendants & codes, hierarchy, r)
            rules.extend(sub_definition.rules)

        # Remove any rules that are included unnecessarily.
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

        included_codes = {rule.code for rule in rules if not rule.code_is_excluded}
        for rule in rules:
            if rule.applies_to_descendants:
                included_codes -= hierarchy.descendants(rule.code)
        rules = [
            rule
            for rule in rules
            if rule.code_is_excluded or rule.code in included_codes
        ]

        return cls(rules)


class DefinitionRule:
    """An element of a definition.  Indicates whether a given code is included or
    excluded in a list of codes, and whether the inclusion/exclusion applies to the
    code's descendants too.
    """

    def __init__(self, code, code_is_excluded=False, applies_to_descendants=False):
        self.code = code
        self.code_is_excluded = code_is_excluded
        self.applies_to_descendants = applies_to_descendants

        self.fragment = str(self.code)
        if self.code_is_excluded:
            self.fragment = "~" + self.fragment
        if self.applies_to_descendants:
            self.fragment = self.fragment + "<"

    def __str__(self):
        return self.fragment

    def __repr__(self):
        return f"[DefinitionRule {self.fragment}]"

    def __eq__(self, other):
        return type(self) == type(other) and self.fragment == other.fragment

    def __hash__(self):
        return hash(self.fragment)

    @classmethod
    def from_fragment(cls, fragment):
        """Build DefinitionRule from string fragment.

        The fragment will have one of the following formats:

        * "XYZ" -- XYZ is included
        * "XYZ<" -- XYZ is included with all its descendants
        * "~XYZ" -- XYZ is excluded
        * "~XYZ<" -- XYZ is excluded with all its descendants
        """

        if fragment[0] == "~":
            code_is_excluded = True
            fragment = fragment[1:]
        else:
            code_is_excluded = False

        if fragment[-1] == "<":
            applies_to_descendants = True
            fragment = fragment[:-1]
        else:
            applies_to_descendants = False

        return cls(
            fragment,
            code_is_excluded=code_is_excluded,
            applies_to_descendants=applies_to_descendants,
        )


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

    elements = sorted(definition.unnegated_elements(), key=sort_key)
    excluded = sorted(definition.negated_elements(), key=sort_key)

    return list(iter_definitions(elements, code_to_name, descendants_map, excluded))
