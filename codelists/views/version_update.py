from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse

from .. import actions
from ..forms import CodelistVersionForm
from ..models import CodelistVersion

template_name = "codelists/version_update.html"


@login_required
def version_update(request, organisation_slug, codelist_slug, qualified_version_str):
    if qualified_version_str[-6:] == "-draft":
        expect_draft = True
        version_str = qualified_version_str[:-6]
    else:
        expect_draft = False
        version_str = qualified_version_str

    version = get_object_or_404(
        CodelistVersion.objects.select_related("codelist"),
        codelist__organisation_id=organisation_slug,
        codelist__slug=codelist_slug,
        version_str=version_str,
    )

    if expect_draft != version.is_draft:
        return redirect(version)

    if request.method == "POST":
        return handle_post(request, version)
    return handle_get(request, version)


def handle_get(request, version):
    ctx = {
        "form": CodelistVersionForm(),
        "version": version,
    }
    return TemplateResponse(request, template_name, ctx)


def handle_post(request, version):
    form = CodelistVersionForm(request.POST, request.FILES)
    if form.is_valid():
        return handle_valid(request, version, form)
    else:
        return handle_invalid(request, version, form)


def handle_valid(request, version, form):
    actions.update_version(version=version, csv_data=form.cleaned_data["csv_data"])

    return redirect(version)


def handle_invalid(request, version, form):
    ctx = {
        "form": form,
        "version": version,
    }
    return TemplateResponse(request, template_name, ctx)
