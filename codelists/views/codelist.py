from django.shortcuts import redirect

from .decorators import load_codelist


@load_codelist
def codelist(request, codelist):
    clv = codelist.versions.order_by("tag").last()
    return redirect(clv)
