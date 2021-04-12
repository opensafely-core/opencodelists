from .hierarchy import Hierarchy


def do_search(coding_system, term=None, code=None):
    assert bool(code) != bool(term)

    if term is not None:
        matching_codes = coding_system.search_by_term(term)
    else:
        matching_codes = coding_system.search_by_code(code)

    hierarchy = Hierarchy.from_codes(coding_system, matching_codes)
    ancestor_codes = hierarchy.filter_to_ultimate_ancestors(matching_codes)

    all_codes = set(ancestor_codes)
    for code in ancestor_codes:
        all_codes |= hierarchy.descendants(code)

    return {
        "all_codes": all_codes,
        "matching_codes": matching_codes,
        "ancestor_codes": ancestor_codes,
    }
