from .definition import Definition
from .hierarchy import Hierarchy


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
    definition = Definition.from_codes(set(clv.codes), hierarchy)
    code_to_term = clv.coding_system.code_to_term(
        hierarchy.nodes | set(clv.all_related_codes)
    )
    rows = [
        (code, code_to_term[code], status)
        for code, status in definition.walk_tree(hierarchy, code_to_term.__getitem__)
    ]
    headers = ["code", "term", "is_included"]
    return [headers] + rows
