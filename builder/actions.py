from collections import defaultdict

import structlog
from django.db import transaction
from django.db.models import Count
from django.utils.text import slugify

from codelists.hierarchy import Hierarchy
from codelists.models import CodeObj, SearchResult

logger = structlog.get_logger()


def create_draft(*, codelist, owner):
    draft = owner.drafts.create(codelist=codelist)
    logger.info("Create draft", draft_pk=draft.pk)
    return draft


@transaction.atomic
def create_draft_with_codes(*, codelist, owner, codes):
    draft = owner.drafts.create(codelist=codelist)
    CodeObj.objects.bulk_create(CodeObj(version=draft, code=code) for code in codes)
    logger.info("Create draft with codes", draft_pk=draft.pk)
    return draft


@transaction.atomic
def create_search(*, draft, term, codes):
    search = draft.searches.create(term=term, slug=slugify(term))

    # Ensure that there is a CodeObj object linked to this draft for each code.
    codes_with_existing_code_objs = set(
        draft.code_objs.filter(code__in=codes).values_list("code", flat=True)
    )
    codes_without_existing_code_objs = set(codes) - codes_with_existing_code_objs
    CodeObj.objects.bulk_create(
        CodeObj(version=draft, code=code) for code in codes_without_existing_code_objs
    )

    # Create a SearchResult for each code.
    code_obj_ids = draft.code_objs.filter(code__in=codes).values_list("id", flat=True)
    SearchResult.objects.bulk_create(
        SearchResult(search=search, code_obj_id=id) for id in code_obj_ids
    )

    logger.info("Created Search", search_pk=search.pk)

    return search


@transaction.atomic
def delete_search(*, search):
    # Grab the PK before we delete the instance
    search_pk = search.pk

    # Delete any codes that only belong to this search
    search.version.code_objs.annotate(num_results=Count("results")).filter(
        results__search=search, num_results=1
    ).delete()

    # Delete the search
    search.delete()

    logger.info("Deleted Search", search_pk=search_pk)


@transaction.atomic
def update_code_statuses(*, draft, updates):
    code_to_status = dict(draft.code_objs.values_list("code", "status"))
    h = Hierarchy.from_codes(draft.coding_system, list(code_to_status))
    new_code_to_status = h.update_node_to_status(code_to_status, updates)

    status_to_new_code = defaultdict(list)
    for code, status in new_code_to_status.items():
        status_to_new_code[status].append(code)

    for status, codes in status_to_new_code.items():
        draft.code_objs.filter(code__in=codes).update(status=status)

    logger.info("Updated code statuses", draft_pk=draft.pk)


def save(*, draft):
    """Convert CodelistVersion from something that's in the builder to something that's
    shown on the site.

    All this does is unset the draft_owner attribute.
    """

    assert not draft.code_objs.filter(status__in=["?", "!"]).exists()
    draft.draft_owner = None
    draft.save()


def discard_draft(*, draft):
    """Mark draft as discarded."""

    draft.discarded = True
    draft.save()
