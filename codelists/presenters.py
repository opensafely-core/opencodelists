from django.db.models import Prefetch

from codelists.models import SearchResult


def present_search_results(clv, code_to_term):
    results = []

    for search in clv.searches.prefetch_related(
        Prefetch(
            "results",
            queryset=SearchResult.objects.select_related("code_obj"),
        )
    ).order_by("code", "term"):
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
                "term_or_code": search.term_or_code,
                "rows": rows,
                "num_included": num_included,
                "total": len(rows),
            }
        )

    return results


def present_definition_for_download(clv):
    """Return rows for CSV download of a definition."""

    codeset = clv.codeset
    if not codeset:
        raise ValueError("Codelist version does not have a codeset")

    code_to_term = clv.coding_system.code_to_term(codeset.all_codes())
    rows = [
        (code, code_to_term[code], status)
        for code, status in codeset.walk_defining_tree(code_to_term.__getitem__)
    ]
    headers = ("code", "term", "is_included")
    return [headers] + rows
