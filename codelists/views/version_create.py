from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse

from .. import actions
from ..forms import CodelistVersionForm
from ..models import Codelist

template_name = "codelists/version_create.html"


@login_required
def version_create(request, organisation_slug, codelist_slug):
    codelist = get_object_or_404(
        Codelist.objects.prefetch_related("versions"),
        organisation_id=organisation_slug,
        slug=codelist_slug,
    )

    if request.method == "POST":
        return handle_post(request, codelist)
    return handle_get(request)


def handle_get(request):
    ctx = {"form": CodelistVersionForm()}
    return TemplateResponse(request, template_name, ctx)


def handle_post(request, codelist):
    form = CodelistVersionForm(request.POST, request.FILES)
    if form.is_valid():
        return handle_valid(request, codelist, form)
    else:
        return handle_invalid(request, form)


def handle_valid(request, codelist, form):
    version = actions.create_version(
        codelist=codelist, csv_data=form.cleaned_data["csv_data"]
    )
    return redirect(version)


def handle_invalid(request, form):
    ctx = {"form": form}
    return TemplateResponse(request, template_name, ctx)
