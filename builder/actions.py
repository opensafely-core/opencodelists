from collections import defaultdict

from django.db import transaction
from django.db.models import Count
from django.utils.text import slugify

from codelists import tree_utils


def create_codelist(*, owner, name, coding_system_id):
    return owner.draft_codelists.create(
        name=name, slug=slugify(name), coding_system_id=coding_system_id
    )


@transaction.atomic
def create_search(*, codelist, term, codes):
    search = codelist.searches.create(term=term, slug=slugify(term))
    for code in codes:
        search.results.create(code=codelist.codes.get_or_create(code=code)[0])
    return search


@transaction.atomic
def delete_search(*, search):
    search.delete()
    search.codelist.codes.annotate(num_results=Count("results")).filter(
        num_results=0
    ).delete()


@transaction.atomic
def update_code_statuses(*, codelist, updates):
    print(updates)
    code_to_status = dict(codelist.codes.values_list("code", "status"))
    subtree = tree_utils.build_subtree(codelist.coding_system, list(code_to_status))
    new_code_to_status = tree_utils.update(subtree, code_to_status, updates)

    status_to_new_code = defaultdict(list)
    for code, status in new_code_to_status.items():
        status_to_new_code[status].append(code)

    for status, codes in status_to_new_code.items():
        codelist.codes.filter(code__in=codes).update(status=status)
