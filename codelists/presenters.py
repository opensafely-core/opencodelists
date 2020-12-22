import attr

from .definition2 import Definition2
from .hierarchy import Hierarchy


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


def present_search_results(clv, code_to_term):
    results = []
    for search in clv.searches.prefetch_related(
        "results", "results__code_obj"
    ).order_by("term"):
        rows = [
            {
                "code": result.code_obj.code,
                "term": code_to_term[result.code_obj.code],
                "included": result.code_obj.is_included(),
            }
            for result in search.results.all()
        ]
        rows.sort(key=lambda row: row["term"])
        num_included = len([r for r in rows if r["included"]])
        results.append(
            {
                "term": search.term,
                "rows": rows,
                "num_included": num_included,
                "total": len(rows),
            }
        )

    return results


def present_definition_for_download(clv):
    """Return rows for CSV download of a definition."""

    hierarchy = Hierarchy.from_codes(clv.coding_system, clv.codes)
    definition = Definition2.from_codes(set(clv.codes), hierarchy)
    code_to_term = clv.coding_system.code_to_term(
        hierarchy.nodes | set(clv.all_related_codes)
    )
    rows = [
        (code, code_to_term[code], status)
        for code, status in definition.walk_tree(hierarchy, code_to_term.__getitem__)
    ]
    headers = ["code", "term", "is_included"]
    return [headers] + rows
