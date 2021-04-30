from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from opencodelists.models import Organisation

from ..models import Handle


def index(request, organisation_slug=None):
    handles = Handle.objects.filter(is_current=True)

    q = request.GET.get("q")
    if q:
        handles = handles.filter(Q(name__contains=q) | Q(description__contains=q))

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

    handles = handles.order_by("name")
    codelists = [handle.codelist for handle in handles]
    ctx = {"codelists": codelists, "organisation": organisation, "q": q}
    return render(request, "codelists/index.html", ctx)
