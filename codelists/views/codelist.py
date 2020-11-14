from django.shortcuts import get_object_or_404, redirect

from ..models import Codelist


def codelist(request, organisation_slug, codelist_slug):
    codelist = get_object_or_404(
        Codelist.objects.prefetch_related("versions"),
        organisation=organisation_slug,
        slug=codelist_slug,
    )

    clv = codelist.versions.order_by("version_str").last()
    return redirect(clv)
