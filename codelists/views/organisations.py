from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Exists, OuterRef, Prefetch
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from opencodelists.models import Organisation

from ..models import CodelistVersion, Handle, Status
from .index import (
    current_public_handles,
    search_handles,
)


PAGE_SIZE = 50

SORT_DIRECTION_ASC = "asc"
SORT_DIRECTION_DESC = "desc"
SORT_DIRECTIONS = {SORT_DIRECTION_ASC, SORT_DIRECTION_DESC}

SORT_BY_CREATED_AT = "created_at"
SORT_BY_NAME = "name"
SORT_BY_UPDATED_AT = "updated_at"
SORT_FOR_PUBLISHED = {SORT_BY_NAME, SORT_BY_UPDATED_AT}
SORT_FOR_UNDER_REVIEW = {SORT_BY_NAME, SORT_BY_CREATED_AT}


def organisation_published(
    request: HttpRequest, organisation_slug: str
) -> HttpResponse:
    organisation, handles, q = _get_organisation_handles(request, organisation_slug)
    sort, direction = _get_sort(request, Status.PUBLISHED)
    published_handles = _handles_with_status(
        handles, Status.PUBLISHED
    ).prefetch_related(_current_handle_prefetch("codelist__handles"))
    codelists = _sort_published_codelists(
        [handle.codelist for handle in published_handles], sort, direction
    )

    page_obj = Paginator(codelists, PAGE_SIZE).get_page(request.GET.get("page"))

    ctx = {
        "page_obj": page_obj,
        "pagination": _pagination_context(page_obj, q, (sort, direction)),
        "organisation": organisation,
        "q": q,
        "sort": sort,
        "direction": direction,
        "sort_options": _sort_options_context(q, sort, direction, SORT_FOR_PUBLISHED),
    }
    return render(request, "codelists/organisation_published.html", ctx)


def organisation_review(request: HttpRequest, organisation_slug: str) -> HttpResponse:
    organisation, handles, q = _get_organisation_handles(request, organisation_slug)
    sort, direction = _get_sort(request, Status.UNDER_REVIEW)
    versions = _sort_under_review_versions(
        _under_review_versions(handles), sort, direction
    )

    page_obj = Paginator(versions, PAGE_SIZE).get_page(request.GET.get("page"))

    ctx = {
        "page_obj": page_obj,
        "pagination": _pagination_context(page_obj, q, (sort, direction)),
        "organisation": organisation,
        "q": q,
        "sort": sort,
        "direction": direction,
        "sort_options": _sort_options_context(
            q, sort, direction, SORT_FOR_UNDER_REVIEW
        ),
    }
    return render(request, "codelists/organisation_review.html", ctx)


def _get_organisation_handles(
    request: HttpRequest, organisation_slug: str
) -> tuple[Organisation, QuerySet[Handle], str | None]:
    """Resolve the organisation and apply the shared public/search filters"""

    organisation = get_object_or_404(Organisation, slug=organisation_slug)
    handles = current_public_handles().filter(organisation=organisation)
    query = request.GET.get("q")
    handles = search_handles(handles, query)
    return organisation, handles, query


def _handles_with_status(handles: QuerySet[Handle], status: Status) -> QuerySet[Handle]:
    """Keep handle rows unique while checking for any matching version"""

    has_version_with_status = CodelistVersion.objects.filter(
        codelist_id=OuterRef("codelist_id"),
        status=status,
    )

    return handles.filter(Exists(has_version_with_status)).select_related("codelist")


def _under_review_versions(handles: QuerySet[Handle]) -> list[CodelistVersion]:
    """Fetch under-review versions for the already-filtered current handles"""

    under_review_versions = (
        CodelistVersion.objects.filter(status=Status.UNDER_REVIEW)
        .select_related("codelist")
        .prefetch_related(_current_handle_prefetch("codelist__handles"))
    )
    handles = _handles_with_status(handles, Status.UNDER_REVIEW).prefetch_related(
        Prefetch(
            "codelist__versions",
            queryset=under_review_versions,
            to_attr="_under_review_versions",
        )
    )

    return [
        version
        for handle in handles
        for version in handle.codelist._under_review_versions
    ]


def _current_handle_prefetch(lookup: str) -> Prefetch:
    """Prefetch current_handle data used by codelist name and URL helpers"""

    return Prefetch(
        lookup,
        queryset=Handle.objects.filter(is_current=True).select_related("organisation"),
    )


def _get_sort(request: HttpRequest, status: Status) -> tuple[str, str]:
    direction = request.GET.get("direction", SORT_DIRECTION_ASC)
    if direction not in SORT_DIRECTIONS:
        direction = SORT_DIRECTION_ASC

    sort_options_by_status = {
        Status.PUBLISHED: SORT_FOR_PUBLISHED,
        Status.UNDER_REVIEW: SORT_FOR_UNDER_REVIEW,
    }
    sort_options = sort_options_by_status.get(status, {SORT_BY_NAME})

    sort = request.GET.get("sort", SORT_BY_NAME)
    if sort not in sort_options:
        sort = SORT_BY_NAME

    return sort, direction


def _sort_published_codelists(codelists, sort: str, direction: str):
    sort_key_funcs = {
        SORT_BY_NAME: lambda codelist: codelist.name.casefold(),
        SORT_BY_UPDATED_AT: lambda codelist: codelist.updated_at,
    }

    return sorted(
        codelists,
        key=sort_key_funcs[sort],
        reverse=direction == SORT_DIRECTION_DESC,
    )


def _sort_under_review_versions(versions, sort: str, direction: str):
    sort_key_funcs = {
        SORT_BY_NAME: lambda version: version.codelist.name.casefold(),
        SORT_BY_CREATED_AT: lambda version: version.created_at,
    }

    return sorted(
        versions,
        key=sort_key_funcs[sort],
        reverse=direction == SORT_DIRECTION_DESC,
    )


def _pagination_context(page_obj, q: str | None, sort_state: tuple[str, str]):
    paginator = page_obj.paginator
    sort, direction = sort_state

    def url_for(page_number: int) -> str:
        params = {
            "page": page_number,
            "q": q or "",
            "sort": sort,
            "direction": direction,
        }
        return f"?{urlencode(params)}"

    return {
        "previous_url": (
            url_for(page_obj.previous_page_number())
            if page_obj.has_previous()
            else None
        ),
        "next_url": url_for(page_obj.next_page_number())
        if page_obj.has_next()
        else None,
        "first_url": url_for(1),
        "last_url": url_for(paginator.num_pages),
        "page_links": [
            {"number": page_number, "url": url_for(page_number)}
            for page_number in paginator.page_range
        ],
    }


def _sort_options_context(
    q: str | None, current_sort: str, current_direction: str, sort_options: set[str]
) -> dict[str, dict[str, str]]:
    return {
        sort: _sort_context(q, current_sort, current_direction, sort)
        for sort in sort_options
    }


def _sort_context(
    q: str | None, current_sort: str, current_direction: str, sort: str
) -> dict[str, str]:
    direction = SORT_DIRECTION_ASC
    if current_sort == sort and current_direction == SORT_DIRECTION_ASC:
        direction = SORT_DIRECTION_DESC

    aria = "none"
    icon = "none"
    if current_sort == sort:
        icon = current_direction
        aria = "ascending" if current_direction == SORT_DIRECTION_ASC else "descending"

    params = {
        "q": q or "",
        "sort": sort,
        "direction": direction,
    }

    return {
        "aria": aria,
        "icon": icon,
        "url": f"?{urlencode(params)}",
    }
