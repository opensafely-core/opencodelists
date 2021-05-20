from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from .. import actions
from ..forms import CodelistVersionForm
from .decorators import load_codelist, require_permission

template_name = "codelists/version_upload.html"


@login_required
@load_codelist
@require_permission
def version_upload(request, codelist):
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
    version = actions.create_old_style_version(
        codelist=codelist, csv_data=form.cleaned_data["csv_data"]
    )
    return redirect(version)


def handle_invalid(request, form):
    ctx = {"form": form}
    return TemplateResponse(request, template_name, ctx)
