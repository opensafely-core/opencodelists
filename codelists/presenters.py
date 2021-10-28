def present_search_results(clv, code_to_term):
    results = []
    for search in clv.searches.prefetch_related(
        "results", "results__code_obj"
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
    code_to_term = clv.coding_system.code_to_term(codeset.all_codes())
    rows = [
        (code, code_to_term[code], status)
        for code, status in codeset.walk_defining_tree(code_to_term.__getitem__)
    ]
    headers = ("code", "term", "is_included")
    return [headers] + rows


# def present_tree_structure(
#     codes, coding_system, hierarchy, code_to_term, code_to_status, depth
# ):
#     sort_key = code_to_term.__getitem__

#     def tree_helper(code, pipes, is_last_sibling, depth):
#         pipe = "└" if is_last_sibling else "├"
#         data = {
#             "code": code,
#             "term": code_to_term[code],
#             "status": code_to_status[code],
#             "pipes": (pipes + [pipe])[1:],
#         }

#         if code not in hierarchy.child_map:
#             data["expandable"] = False
#         elif depth == 0:
#             data["expandable"] = True
#             data["expanded"] = False
#         else:
#             child_codes = hierarchy.child_map[code]
#             pipe = " " if is_last_sibling else "│"
#             data["expandable"] = True
#             data["expanded"] = True
#             data["children"] = [
#                 tree_helper(
#                     child_code, pipes + [pipe], ix == (len(child_codes) - 1), depth - 1
#                 )
#                 for ix, child_code in enumerate(sorted(child_codes, key=sort_key))
#             ]

#         return data

#     ancestor_codes = hierarchy.filter_to_ultimate_ancestors(set(codes))

#     sections = []

#     for section_heading, section_ancestor_codes in sorted(
#         coding_system.codes_by_type(ancestor_codes, hierarchy).items()
#     ):
#         trees = [
#             tree_helper(code, [], ix == len(section_ancestor_codes), depth)
#             for ix, code in enumerate(sorted(section_ancestor_codes, key=sort_key))
#         ]
#         sections.append({"heading": section_heading, "trees": trees})

#     return sections


def present_tree_ancestors(codes, coding_system, hierarchy, code_to_term):
    sort_key = code_to_term.__getitem__
    ancestor_codes = hierarchy.filter_to_ultimate_ancestors(set(codes))

    return [
        {"heading": type, "ancestor_codes": sorted(codes, key=sort_key)}
        for type, codes in sorted(
            coding_system.codes_by_type(ancestor_codes, hierarchy).items()
        )
    ]
