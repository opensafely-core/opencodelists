from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from opencodelists.models import Organisation

from ..models import Codelist


def index(request, organisation_slug=None):
    codelists = Codelist.objects.all()

    q = request.GET.get("q")
    if q:
        codelists = codelists.filter(Q(name__contains=q) | Q(description__contains=q))

    if organisation_slug:
        organisation = get_object_or_404(Organisation, slug=organisation_slug)
        codelists = codelists.filter(organisation=organisation)
    else:
        organisation = None
        # For now, we only want to show codelists that were created as part of the
        # OpenSAFELY organisation.
        codelists = codelists.filter(
            organisation_id__in=["opensafely", "primis-covid19-vacc-uptake"]
        )

    codelists = codelists.order_by("name")
    ctx = {"codelists": codelists, "organisation": organisation, "q": q}
    return render(request, "codelists/index.html", ctx)
