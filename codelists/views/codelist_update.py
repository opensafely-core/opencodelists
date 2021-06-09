from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from .. import actions
from ..forms import CodelistUpdateForm, ReferenceFormSet, SignOffFormSet
from .decorators import load_codelist, require_permission

template_name = "codelists/codelist.html"


@login_required
@load_codelist
@require_permission
def codelist_update(request, codelist):
    if request.method == "POST":
        return handle_post(request, codelist)
    return handle_get(request, codelist)


def handle_get(request, codelist):
    codelist_form = CodelistUpdateForm(
        {
            "coding_system_id": codelist.coding_system_id,
            "description": codelist.description,
            "methodology": codelist.methodology,
        }
    )

    reference_formset = ReferenceFormSet(
        queryset=codelist.references.all(), prefix="reference"
    )
    signoff_formset = SignOffFormSet(queryset=codelist.signoffs.all(), prefix="signoff")

    ctx = {
        "codelist_form": codelist_form,
        "reference_formset": reference_formset,
        "signoff_formset": signoff_formset,
    }
    return TemplateResponse(request, template_name, ctx)


def handle_post(request, codelist):
    codelist_form = CodelistUpdateForm(request.POST, request.FILES)
    reference_formset = ReferenceFormSet(
        request.POST, queryset=codelist.references.all(), prefix="reference"
    )
    signoff_formset = SignOffFormSet(
        request.POST, queryset=codelist.signoffs.all(), prefix="signoff"
    )

    if (
        codelist_form.is_valid()
        and reference_formset.is_valid()
        and signoff_formset.is_valid()
    ):
        return handle_valid(
            request, codelist, codelist_form, reference_formset, signoff_formset
        )
    else:
        return handle_invalid(
            request, codelist_form, reference_formset, signoff_formset
        )


@transaction.atomic
def handle_valid(request, codelist, codelist_form, reference_formset, signoff_formset):
    references = [
        {"url": reference["url"], "text": reference["text"]}
        for reference in reference_formset.cleaned_data
        if reference and not reference["DELETE"]
    ]

    signoffs = [
        {"user": signoff["user"], "date": signoff["date"]}
        for signoff in signoff_formset.cleaned_data
        if signoff and not signoff["DELETE"]
    ]

    codelist = actions.update_codelist(
        codelist=codelist,
        description=codelist_form.cleaned_data["description"],
        methodology=codelist_form.cleaned_data["methodology"],
        references=references,
        signoffs=signoffs,
    )

    return redirect(codelist)


def handle_invalid(request, codelist_form, reference_formset, signoff_formset):
    ctx = {
        "codelist_form": codelist_form,
        "reference_formset": reference_formset,
        "signoff_formset": signoff_formset,
    }
    return TemplateResponse(request, template_name, ctx)
