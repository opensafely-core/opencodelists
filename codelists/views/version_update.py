from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from .. import actions
from ..forms import CodelistVersionForm
from .decorators import load_version, require_permission

template_name = "codelists/version_update.html"


@login_required
@load_version
@require_permission
def version_update(request, version):
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
