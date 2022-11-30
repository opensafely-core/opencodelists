from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from .. import actions
from ..coding_systems import most_recent_database_alias
from ..forms import CodelistVersionForm
from .decorators import load_codelist, require_permission

template_name = "codelists/version_upload.html"


@login_required
@load_codelist
@require_permission
def version_upload(request, codelist):
    if request.method == "POST":
        return handle_post(request, codelist)
    return handle_get(request, codelist.coding_system_id)


def handle_get(request, coding_system_id):
    ctx = {"form": CodelistVersionForm(coding_system_id=coding_system_id)}
    return TemplateResponse(request, template_name, ctx)


def handle_post(request, codelist):
    form = CodelistVersionForm(request.POST, request.FILES)
    if form.is_valid():
        return handle_valid(request, codelist, form)
    else:
        return handle_invalid(request, form)


def handle_valid(request, codelist, form):
    # TODO: Retrieve coding system database alias from form input when
    # coding system version is selectable
    version = actions.create_old_style_version(
        codelist=codelist,
        csv_data=form.cleaned_data["csv_data"],
        coding_system_database_alias=most_recent_database_alias(
            codelist.coding_system_id
        ),
    )
    return redirect(version)


def handle_invalid(request, form):
    ctx = {"form": form}
    return TemplateResponse(request, template_name, ctx)
