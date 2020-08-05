from collections import defaultdict

from django.db import transaction

from .models import SearchResult


def create_codelist(*, owner, name, coding_system_id):
    return owner.draft_codelists.create(name=name, coding_system_id=coding_system_id)


@transaction.atomic
def create_search(*, codelist, term, results):
    search = codelist.searches.create(term=term)
    search.results.bulk_create(
        SearchResult(
            search=search,
            code=code,
            matches_term=(code in results["matching_codes"]),
            is_ancestor=(code in results["ancestor_codes"]),
        )
        for code in results["all_codes"]
    )
    return search


@transaction.atomic
def update_search(*, results, updates, code_to_status, ancestors_map, descendants_map):
    def get_status(code):
        return code_to_updated_status.get(code, code_to_status[code])

    def is_directly_related(code1, code2):
        return (
            code1 == code2
            or code1 in descendants_map[code2]
            or code2 in descendants_map[code1]
        )

    code_to_updated_status = {}

    for update in updates:
        code, status = update["code"], update["status"]
        code_to_updated_status[code] = status

        descendant_status = {"+": "(+)", "-": "(-)"}[status]
        conflicting_status = {"+": "-", "-": "+"}[status]

        for descendant_code in descendants_map[code]:
            if any(
                get_status(ancestor_code) == conflicting_status
                and not is_directly_related(code, ancestor_code)
                for ancestor_code in ancestors_map[descendant_code]
            ):
                code_to_updated_status[descendant_code] = "!"
            else:
                code_to_updated_status[descendant_code] = descendant_status

    updated_status_to_code = defaultdict(list)
    for code, status in code_to_updated_status.items():
        updated_status_to_code[status].append(code)

    for status, codes in updated_status_to_code.items():
        results.filter(code__in=codes).update(status=status)
