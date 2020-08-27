from django.urls import reverse

from . import tree_utils


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

    def codes(self, tree):
        """Return set of codes that is defined by the rules.
        """

        codes = set()
        descendants_map = tree_utils.build_descendants_map(tree)

        for rule in self.including_rules():
            codes.add(rule.code)

            if rule.applies_to_descendants:
                codes |= descendants_map[rule.code]

        for rule in self.excluding_rules():
            try:
                codes.remove(rule.code)
            except KeyError:
                # Sometimes a code can be excluded by more than one rule.
                pass

            if rule.applies_to_descendants:
                codes -= descendants_map[rule.code]

        return codes

    @classmethod
    def from_query(cls, fragments):
        """Build definition from list of string fragments.

        See DefinitionRule.from_fragment for expected format of each fragment.
        """

        rules = [DefinitionRule.from_fragment(f) for f in fragments]
        return cls(rules)

    @classmethod
    def from_codes(cls, codes, tree, r=0.25):
        """Build definition from collection of codes.

        This code will change significantly in an upcoming commit, when it will have a
        proper docstring.
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
                        yield DefinitionRule(code, applies_to_descendants=True)
                        yield from negative_helper(tree[code])
                    else:
                        yield DefinitionRule(code)
                        yield from helper(tree[code])
                else:
                    yield from helper(tree[code])

        def negative_helper(tree):
            for code in sorted(tree):
                if code not in codes:
                    descendants = descendants_map[code]
                    if descendants and not descendants & codes:
                        yield DefinitionRule(
                            code, code_is_excluded=True, applies_to_descendants=True
                        )
                    else:
                        yield DefinitionRule(code, code_is_excluded=True)
                        yield from negative_helper(tree[code])
                else:
                    yield from negative_helper(tree[code])

        rules = list(helper(tree))

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
                included_codes -= descendants_map[rule.code]
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


def build_html_definition(coding_system, subtree, definition):
    """Render a Definition as HTML.

    This code will change significantly in an upcoming commit, when it will have a
    proper docstring.
    """

    code_to_name = coding_system.lookup_names([rule.code for rule in definition.rules])
    descendants_map = tree_utils.build_descendants_map(subtree)

    def sort_key(rule):
        return code_to_name[rule.code]

    lines = ["<ul>"]

    for rule in sorted(definition.including_rules(), key=sort_key):
        name = code_to_name[rule.code]
        url = reverse(f"{coding_system.id}:concept", args=[rule.code])
        style = "color: blue"

        if rule.applies_to_descendants:
            matching_excluding_rules = [
                excluding_rule
                for excluding_rule in definition.excluding_rules()
                if excluding_rule.code in descendants_map[rule.code]
            ]

            if matching_excluding_rules:
                lines.append(
                    f'<li><a href="{url}" style="{style}">{name}</a> (<code>{rule.code}</code>) and all descendants except:</li>'
                )
                lines.append('<ul class="mb-0">')

                for excluding_rule in sorted(matching_excluding_rules, key=sort_key):
                    name = code_to_name[excluding_rule.code]
                    url = reverse(
                        f"{coding_system.id}:concept", args=[excluding_rule.code]
                    )
                    style = "color: black"

                    if excluding_rule.applies_to_descendants:
                        lines.append(
                            f'<li><a href="{url}" style="{style}">{name}</a> (<code>{excluding_rule.code}</code>) and all descendants</li>'
                        )
                    else:
                        lines.append(
                            f'<li><a href="{url}" style="{style}">{name}</a> (<code>{excluding_rule.code}</code>)</li>'
                        )

                lines.append("</ul>")

            else:
                lines.append(
                    f'<li><a href="{url}" style="{style}">{name}</a> (<code>{rule.code}</code>) and all descendants</li>'
                )

        else:
            lines.append(
                f'<li><a href="{url}" style="{style}">{name}</a> (<code>{rule.code}</code>)</li>'
            )

    lines.append("</ul>")

    return "\n".join(lines)
