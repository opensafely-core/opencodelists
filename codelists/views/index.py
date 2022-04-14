from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from opencodelists.list_utils import flatten
from opencodelists.models import Organisation

from opentelemetry import trace

from ..models import Handle, Status


def index(request, organisation_slug=None, status=Status.PUBLISHED):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("index"):
        with tracer.start_as_current_span("handles"):
            handles = Handle.objects.filter(is_current=True)

        with tracer.start_as_current_span("q"):
            q = request.GET.get("q")
            if q:
                handles = handles.filter(
                    Q(name__contains=q) | Q(codelist__description__contains=q)
                )

        with tracer.start_as_current_span("organisation_slug"):
            if organisation_slug:
                organisation = get_object_or_404(Organisation, slug=organisation_slug)
                handles = handles.filter(organisation=organisation)
            else:
                organisation = None
                # For now, we only want to show codelists that were created as part of the
                # OpenSAFELY organisation.
                handles = handles.filter(
                    organisation_id__in=["opensafely", "primis-covid19-vacc-uptake"]
                )

        with tracer.start_as_current_span("handles"):
            handles = handles.order_by("name")

        page_number = request.GET.get("page")
        with tracer.start_as_current_span("status") as status_span:
            if status == Status.PUBLISHED:
                status_span.set_attribute("codelist_status", "published")
                codelists = _all_published_codelists(handles)
                ctx = {
                    "codelists_page": _get_page_obj(codelists, page_number, 15),
                    "organisation": organisation,
                    "q": q,
                }
                return render(request, "codelists/index.html", ctx)
            else:
                status_span.set_attribute("codelist_status", "under review")
                assert status == Status.UNDER_REVIEW
                versions = _all_under_review_codelist_versions(handles)
                ctx = {
                    "versions_page": _get_page_obj(versions, page_number),
                    "organisation": organisation,
                    "q": q,
                    "page_obj": _get_page_obj(versions, page_number),
                }
                return render(request, "codelists/under_review_index.html", ctx)


def _get_page_obj(objects, page_number, paginate_by=30):
    paginator = Paginator(objects, paginate_by)
    page_obj = paginator.get_page(page_number)
    return page_obj


def _all_published_codelists(handles):
    return [
        handle.codelist
        for handle in handles
        if handle.codelist.has_published_versions()
    ]


def _all_under_review_codelist_versions(handles):
    return flatten(
        [
            list(handle.codelist.versions.filter(status=Status.UNDER_REVIEW))
            for handle in handles
        ]
    )
