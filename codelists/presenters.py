from itertools import groupby

import attr
from django.urls import reverse


@attr.s
class DefinitionRow:
    """
    Data structure for a Definition to prepare for display

    name: name of the definition
    code: code of the definition
    excluded_descendants: list of excluded children (created with this class too)
    all_descendants: are all of this Definitions descendants included?

    Between all_descendants and excluded_descendants we can cover the three state
    situation a DefinitionRow can be in:

        * all descendants are included (all_descendants = True, excluded_descendants = [])
        * all descendants except N (all_descendants = True, excluded_descendants = [...])
        * no descendants (all_descendants = False, excluded_descendants ignored)

    """

    name: str = attr.ib()
    code: str = attr.ib()
    excluded_descendants: list = attr.ib(default=list())
    all_descendants: bool = attr.ib(default=True)


def _iter_rules(hierarchy, rules, name_for_rule, excluded):
    for rule in rules:
        row = DefinitionRow(
            name=name_for_rule(rule),
            code=rule.code,
            all_descendants=rule.applies_to_descendants,
        )

        # no descendents for this code so we can shortcut the iteration here
        if not rule.applies_to_descendants:
            yield attr.asdict(row)
            continue

        # filter the excluded rules down to children of the current Rule
        excluding_rules = [
            r for r in excluded if r.code in hierarchy.descendants(rule.code)
        ]

        # generate excluded children by recursing into this function
        row.excluded_descendants = [
            DefinitionRow(
                name=name_for_rule(rule),
                code=rule.code,
                all_descendants=rule.applies_to_descendants,
            )
            for rule in excluding_rules
        ]

        yield attr.asdict(row)


def build_definition_rows(coding_system, hierarchy, definition):
    code_to_name = coding_system.lookup_names([rule.code for rule in definition.rules])

    def name_for_rule(rule):
        return code_to_name.get(rule.code, "Unknown code (a TPP Y-code?)")

    included_rules = sorted(definition.including_rules(), key=name_for_rule)
    excluded_rules = sorted(definition.excluding_rules(), key=name_for_rule)

    return list(_iter_rules(hierarchy, included_rules, name_for_rule, excluded_rules))


def build_html_tree_highlighting_codes(coding_system, hierarchy, definition):
    codes = definition.codes(hierarchy)
    codes_in_definition = {r.code for r in definition.including_rules()}
    codes_in_hierarchy = hierarchy.nodes
    code_to_name = coding_system.lookup_names(codes_in_hierarchy)
    sort_key = code_to_name.__getitem__

    lines = []
    last_direction = 1
    for node in hierarchy.walk_depth_first_as_tree(sort_key=sort_key):
        direction = node.direction
        code = node.label

        if direction == last_direction == 1:
            lines.append("<ul>")
        elif direction == last_direction == -1:
            lines.append("</ul>")

        last_direction = direction

        if direction == -1:
            continue

        if code in codes:
            colour = "blue"
        else:
            colour = "black"

        style = f"color: {colour}"

        if code in codes_in_definition:
            style += "; text-decoration: underline"

        name = code_to_name[code]
        url = reverse(f"{coding_system.id}:concept", args=[code])

        lines.append(
            f'<li><a href="{url}" style="{style}">{name}</a> (<code>{code}</code>)</li>'
        )

    return "\n".join(lines)


def tree_tables(ancestor_codes, hierarchy, code_to_term, code_to_type, code_to_status):
    """Return list of tables of codes arranged in trees, grouped by type of code.

    Each table is a dict, with a heading and a list of rows.
    """

    sort_by_type_key = code_to_type.__getitem__
    sort_by_term_key = code_to_term.__getitem__

    type_to_codes = {
        type: list(codes_for_type)
        for type, codes_for_type in groupby(
            sorted(ancestor_codes, key=sort_by_type_key), sort_by_type_key
        )
    }

    tables = []

    for type, codes_for_type in sorted(type_to_codes.items()):
        rows = []

        for ancestor_code in sorted(codes_for_type, key=sort_by_term_key):
            for code, pipes in hierarchy.walk_depth_first_as_tree_with_pipes(
                starting_node=ancestor_code, sort_key=sort_by_term_key
            ):
                rows.append(
                    {
                        "code": code,
                        "status": code_to_status[code],
                        "term": code_to_term[code],
                        "pipes": pipes,
                    }
                )

        table = {
            "heading": type.title(),
            "rows": rows,
        }
        tables.append(table)

    return tables
