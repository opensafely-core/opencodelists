from collections import defaultdict

import structlog
from django.db import transaction
from django.db.models import Count
from django.utils.text import slugify

from codelists.models import CodeObj, SearchResult, Status

logger = structlog.get_logger()


@transaction.atomic
def create_search(*, draft, term=None, code=None, codes):
    assert bool(term) != bool(code)
    if term is not None:
        slug = slugify(term)
    else:
        slug = f"code:{code}"
    search, new = draft.searches.get_or_create(term=term, code=code, slug=slug)
    if not new:
        logger.info("Returned existing Search", search_pk=search.pk)
        return search

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

    from codelists.actions import cache_hierarchy  # avoid circular imports

    cache_hierarchy(version=draft)

    logger.info("Created Search", search_pk=search.pk)

    return search


@transaction.atomic
def delete_search(*, search):
    # Grab the PK before we delete the instance
    search_pk = search.pk

    # Delete any codes that:
    # - only belong to this search
    # - are not included
    # - are not descendants of an included code

    # Find all code objs that belong to this search and no others
    search_only_code_objs = search.version.code_objs.annotate(
        num_results=Count("results")
    ).filter(results__search=search, num_results=1)
    # Get all explicitly included codes on the codelist
    all_included_codes = search.version.codeset.codes()

    # Build a set of codes_to_keep from this search, consisting of any included codes, their descendants,
    # and any codes with ancestor that is included
    hierarchy = search.version.hierarchy
    codes_to_keep = set()

    codes_to_keep = []
    for code_obj in search_only_code_objs:
        ancestors = hierarchy.ancestors(code_obj.code)
        ancestors_in_included = ancestors & all_included_codes
        if ancestors_in_included or code_obj.code in all_included_codes:
            codes_to_keep.append(code_obj.code)

    # Delete any code objs that belong to this search only, and are not in the codes_to_keep set
    search_only_code_objs.exclude(code__in=codes_to_keep).delete()

    # Delete the search
    search.delete()

    logger.info("Deleted Search", search_pk=search_pk)


@transaction.atomic
def update_code_statuses(*, draft, updates):
    new_codeset = draft.codeset.update(updates)

    status_to_new_code = defaultdict(list)
    for code, status in new_codeset.code_to_status.items():
        status_to_new_code[status].append(code)

    for status, codes in status_to_new_code.items():
        draft.code_objs.filter(code__in=codes).update(status=status)

    logger.info("Updated code statuses", draft_pk=draft.pk)


def save(*, draft):
    """Convert CodelistVersion from something that's in the builder to something that's
    under review.
    """

    assert not draft.code_objs.filter(status__in=["?", "!"]).exists()
    draft.status = Status.UNDER_REVIEW
    draft.save()


@transaction.atomic
def discard_draft(*, draft):
    """Delete draft."""

    if draft.codelist.versions.count() == 1:
        draft.codelist.delete()
    else:
        draft.delete()
