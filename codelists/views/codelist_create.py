from django.contrib.auth.decorators import login_required
from django.core.exceptions import NON_FIELD_ERRORS
from django.db.utils import IntegrityError
from django.forms import formset_factory
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from .. import actions
from ..coding_systems import CODING_SYSTEMS
from ..forms import CodelistCreateForm, ReferenceForm, SignOffForm, data_without_delete
from .decorators import load_owner, require_permission

template_name = "codelists/codelist.html"
ReferenceFormSet = formset_factory(ReferenceForm, can_delete=True)
SignOffFormSet = formset_factory(SignOffForm, can_delete=True)


@login_required
@load_owner
@require_permission
def codelist_create(request, owner):
    if request.method == "POST":
        return handle_post(request, owner)
    return handle_get(request)


def handle_get(request):
    ctx = {
        "codelist_form": CodelistCreateForm(),
        "reference_formset": ReferenceFormSet(prefix="reference"),
        "signoff_formset": SignOffFormSet(prefix="signoff"),
    }
    return TemplateResponse(request, template_name, ctx)


def handle_post(request, owner):
    codelist_form = CodelistCreateForm(request.POST, request.FILES)
    reference_formset = ReferenceFormSet(
        request.POST, request.FILES, prefix="reference"
    )
    signoff_formset = SignOffFormSet(request.POST, request.FILES, prefix="signoff")

    if (
        codelist_form.is_valid()
        and reference_formset.is_valid()
        and signoff_formset.is_valid()
    ):
        return handle_valid(
            request, owner, codelist_form, reference_formset, signoff_formset
        )
    else:
        return handle_invalid(
            request, codelist_form, reference_formset, signoff_formset
        )


def handle_valid(request, owner, codelist_form, reference_formset, signoff_formset):
    # get changed forms so we ignore empty form instances
    references = (
        data_without_delete(f.cleaned_data)
        for f in reference_formset
        if f.has_changed()
    )
    signoffs = (
        data_without_delete(f.cleaned_data) for f in signoff_formset if f.has_changed()
    )

    name = codelist_form.cleaned_data["name"]

    # TODO: Retrieve coding system database alias from form input when
    # coding system version is selectable
    coding_system_id = codelist_form.cleaned_data["coding_system_id"]
    coding_system_database_alias = (
        CODING_SYSTEMS[coding_system_id].most_recent().database_alias
    )

    try:
        codelist = actions.create_old_style_codelist(
            owner=owner,
            name=name,
            coding_system_id=coding_system_id,
            coding_system_database_alias=coding_system_database_alias,
            description=codelist_form.cleaned_data["description"],
            methodology=codelist_form.cleaned_data["methodology"],
            csv_data=codelist_form.cleaned_data["csv_data"],
            references=references,
            signoffs=signoffs,
        )
    except IntegrityError as e:
        assert "UNIQUE constraint failed" in str(e)
        codelist_form.add_error(
            NON_FIELD_ERRORS,
            f"There is already a codelist called {name}",
        )
        return handle_invalid(
            request, codelist_form, reference_formset, signoff_formset
        )

    return redirect(codelist)


def handle_invalid(request, codelist_form, reference_formset, signoff_formset):
    ctx = {
        "codelist_form": codelist_form,
        "reference_formset": reference_formset,
        "signoff_formset": signoff_formset,
    }
    return TemplateResponse(request, template_name, ctx)
