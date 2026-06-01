from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render

from opencodelists.list_utils import flatten
from opencodelists.models import Organisation

from ..models import CodelistVersion, Status
from .index import (
    _all_published_codelists,
    _current_public_handles,
    _get_page_obj,
    _search_handles,
)


def organisation_published(request, organisation_slug):
    organisation = get_object_or_404(Organisation, slug=organisation_slug)
    handles = _current_public_handles().filter(organisation=organisation)
    handles, q = _search_handles(handles, request.GET.get("q"))
    codelists = _all_published_codelists(handles)
    ctx = {
        "codelists_page": _get_page_obj(codelists, request.GET.get("page"), 15),
        "organisation": organisation,
        "q": q,
    }
    return render(request, "codelists/organisation_published.html", ctx)


def organisation_review(request, organisation_slug):
    organisation = get_object_or_404(Organisation, slug=organisation_slug)
    handles = _current_public_handles().filter(organisation=organisation)
    handles, q = _search_handles(handles, request.GET.get("q"))
    versions = _all_under_review_codelist_versions(handles)
    versions_page = _get_page_obj(versions, request.GET.get("page"))
    ctx = {
        "versions_page": versions_page,
        "organisation": organisation,
        "q": q,
        "page_obj": versions_page,
    }
    return render(request, "codelists/organisation_review.html", ctx)


_under_review_prefetch = Prefetch(
    "codelist__versions",
    queryset=CodelistVersion.objects.filter(
        status=Status.UNDER_REVIEW,
    ),
    to_attr="_under_review_versions",
)


def _all_under_review_codelist_versions(handles):
    handles = (
        handles.filter(codelist__versions__status=Status.UNDER_REVIEW)
        .select_related("codelist")
        .distinct()
        .prefetch_related(_under_review_prefetch)
    )

    return flatten(handle.codelist._under_review_versions for handle in handles)
