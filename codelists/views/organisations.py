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


def organisation_published(
    request: HttpRequest, organisation_slug: str
) -> HttpResponse:
    organisation, handles, q = _get_organisation_handles(request, organisation_slug)
    published_handles = _handles_with_status(
        handles, Status.PUBLISHED
    ).prefetch_related(_current_handle_prefetch("codelist__handles"))
    codelists = [handle.codelist for handle in published_handles]

    ctx = {
        "page_obj": Paginator(codelists, PAGE_SIZE).get_page(request.GET.get("page")),
        "organisation": organisation,
        "q": q,
    }
    return render(request, "codelists/organisation_published.html", ctx)


def organisation_review(request: HttpRequest, organisation_slug: str) -> HttpResponse:
    organisation, handles, q = _get_organisation_handles(request, organisation_slug)
    versions = _under_review_versions(handles)

    ctx = {
        "page_obj": Paginator(versions, PAGE_SIZE).get_page(request.GET.get("page")),
        "organisation": organisation,
        "q": q,
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
