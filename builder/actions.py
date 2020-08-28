from collections import defaultdict

import structlog
from django.db import transaction
from django.db.models import Count
from django.utils.text import slugify

from codelists.hierarchy import Hierarchy

logger = structlog.get_logger()


def create_codelist(*, owner, name, coding_system_id):
    codelist = owner.draft_codelists.create(
        name=name, slug=slugify(name), coding_system_id=coding_system_id
    )

    logger.info("Create Codelist", codelist_pk=codelist.pk)

    return codelist


@transaction.atomic
def create_search(*, codelist, term, codes):
    search = codelist.searches.create(term=term, slug=slugify(term))
    for code in codes:
        search.results.create(code=codelist.codes.get_or_create(code=code)[0])

    logger.info("Created Search", search_pk=search.pk)

    return search


@transaction.atomic
def delete_search(*, search):
    # Grab the PK before we delete the instance
    search_pk = search.pk

    search.delete()
    search.codelist.codes.annotate(num_results=Count("results")).filter(
        num_results=0
    ).delete()

    logger.info("Deleted Search", search_pk=search_pk)


@transaction.atomic
def update_code_statuses(*, codelist, updates):
    code_to_status = dict(codelist.codes.values_list("code", "status"))
    h = Hierarchy.from_codes(codelist.coding_system, list(code_to_status))
    new_code_to_status = h.update_node_to_status(code_to_status, updates)

    status_to_new_code = defaultdict(list)
    for code, status in new_code_to_status.items():
        status_to_new_code[status].append(code)

    for status, codes in status_to_new_code.items():
        codelist.codes.filter(code__in=codes).update(status=status)

    logger.info("Updated Codelist Statuses", codelist_pk=codelist.pk)
