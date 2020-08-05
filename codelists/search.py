from . import tree_utils


def do_search(coding_system, term):
    assert coding_system.id == "snomedct"

    matching_codes = coding_system.search(term)
    subtree = tree_utils.build_subtree(coding_system, list(matching_codes))
    descendants_map = tree_utils.build_descendants_map(subtree)

    ancestors_map = {}
    for ancestor, descendants in descendants_map.items():
        for descendant in descendants:
            if descendant not in ancestors_map:
                ancestors_map[descendant] = set()
            ancestors_map[descendant].add(ancestor)

    ancestor_codes = [
        code for code in matching_codes if not matching_codes & ancestors_map[code]
    ]

    all_codes = set(ancestor_codes)
    for code in ancestor_codes:
        all_codes |= descendants_map[code]

    return {
        "all_codes": all_codes,
        "matching_codes": matching_codes,
        "ancestor_codes": ancestor_codes,
    }
