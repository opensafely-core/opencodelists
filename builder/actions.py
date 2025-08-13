from collections import defaultdict

import structlog
from django.db import transaction
from django.db.models import Count
from django.utils.text import slugify

from codelists.models import CodeObj, SearchResult, Status
from coding_systems.base.import_data_utils import check_and_update_compatibile_versions
from coding_systems.versioning.models import CodingSystemRelease


class DraftNotReadyError(Exception):
    pass


logger = structlog.get_logger()


def create_search_slug(term: str, code: str) -> str:
    """
    Returns the search slug which is either the slugified search term,
    or the code prefixed with "code:". Also validates that only one of
    term and code is set.

    Note that the result is not guaranteed to match Django's regex for a slug
    [-a-zA-Z0-9_]+ for codes: it includes a colon to ensure we can distinguish
    it from a term, and may include non-slug characters such as ! or spaces.
    This behaviour is partly present for backwards compatibility (for example,
    changing the slugs for existing searches might require some care).
    """
    assert bool(term) != bool(code)
    if term is not None:
        slug = slugify(term)
    else:
        slug = f"code:{code}"
    return slug


def get_codes_to_keep(codeset_version, potential_codes):
    """
    Identifies which codes, out of a list of potential codes, should be kept when tidying up.
    Returns codes that are:
    1. Explicitly included in the codelist
    2. Descendants of included codes
    """
    # Get all explicitly included codes on the codelist
    all_included_codes = codeset_version.codeset.codes()

    # Build a list of codes_to_keep from this search, consisting of any included codes or their descendants
    hierarchy = codeset_version.hierarchy
    codes_to_keep = []
    for code_obj in potential_codes:
        ancestors = hierarchy.ancestors(code_obj.code)
        ancestors_in_included = ancestors & all_included_codes
        if ancestors_in_included or code_obj.code in all_included_codes:
            codes_to_keep.append(code_obj.code)
    return codes_to_keep


@transaction.atomic
def create_search(*, draft, term=None, code=None, codes):
    if len(codes) > 20000:
        # If we have too many codes then we risk breaching the MAX_VARIABLE_SIZE
        # limit in sqlite in the below queries. However, having too many codes
        # is also a sign that the search is too broad, and we should probably
        # not allow it. The current MAX_VARIABLE_SIZE is 250,000, and the default
        # for sqlite after v3.32.0 (2020-05-22) is 32766, so 20,000 will not hit
        # that limit.
        logger.info(
            "Search request rejected due to large code count",
            code_count=len(codes),
            term=term,
            code=code,
        )

        message = (
            (
                f'Your search for "{term}" returned {len(codes):,} codes, '
                "which exceeds the maximum limit of 20,000. It's likely that "
                "you have searched for a very common term, or one that "
                "appears near the top of the coding system hierarchy. Please "
                "try to refine your search to return fewer results."
            )
            if term
            else (
                f'Your search for code "{code}" returned {len(codes):,} codes, '
                "which exceeds the maximum limit of 20,000. When you search "
                "for a code, we return all codes that are descendants of that "
                "code, so if you search for a code near the top of the coding "
                "system hierarchy you get an unmanageable number of results. "
                "Please try to refine your search to return fewer results."
            )
        )

        return {
            "error": True,
            "message": message,
        }

    slug = create_search_slug(term, code)
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
    codes_to_keep = get_codes_to_keep(search.version, search_only_code_objs)

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

    # It's possible that a user has just unselected, or excluded, an "orphaned" code i.e.
    # one that was included (implicitly or explicitly) from a now deleted search. If we
    # don't remove those codes, then you get into the situation where the only way to remove
    # them is to explicitly include/exclude them - or redo the search that found them, return
    # them to unresolved, and then delete the search.
    # This finds all orphaned codes that aren't explicitly included, and deletes them unless
    # we need to keep them because they have an included ancestor
    orphaned_codes = draft.code_objs.filter(results=None).exclude(status="+")
    codes_to_keep = get_codes_to_keep(draft, orphaned_codes)

    orphaned_codes.exclude(code__in=codes_to_keep).delete()

    logger.info("Updated code statuses", draft_pk=draft.pk)


def save(*, draft):
    """Convert CodelistVersion from something that's in the builder to something that's
    under review.
    """

    if draft.code_objs.filter(status__in=["?", "!"]).exists():
        raise DraftNotReadyError()
    draft.status = Status.UNDER_REVIEW
    draft.save()

    # If there any more recent releases for this version's coding system, check them
    # for compatibility now that the draft has been saved for review.

    # Find more recent releases, in "valid_from" order, oldest to newest
    newer_coding_system_releases = CodingSystemRelease.objects.filter(
        coding_system=draft.coding_system_id,
        valid_from__gt=draft.coding_system_release.valid_from,
    ).order_by("valid_from")

    for coding_system_release in newer_coding_system_releases:
        coding_system = draft.coding_system.get_by_release(
            database_alias=coding_system_release.database_alias
        )
        compatible_count = check_and_update_compatibile_versions(coding_system, [draft])
        # If this release was not found to be compatible, we can stop checking, as
        # we'd expect later releases to also not be compatible
        if compatible_count == 0:
            break


@transaction.atomic
def discard_draft(*, draft):
    """Delete draft."""

    if draft.codelist.versions.count() == 1:
        draft.codelist.delete()
    else:
        draft.delete()
