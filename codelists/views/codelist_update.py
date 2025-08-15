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
    owner_choices = get_owner_choices(codelist, request.user)

    if request.method == "POST":
        return handle_post(request, codelist, owner_choices)
    return handle_get(request, codelist, owner_choices)


def get_owner_choices(codelist, user):
    owner_choices = [(user.owner_identifier, "Me")]

    if codelist.user and codelist.user != user:
        # User is collaborator on codelist owned by another user
        owner_choices.append((codelist.user.owner_identifier, codelist.user.name))

    for organisation in user.organisations.all():
        owner_choices.append((organisation.owner_identifier, organisation.name))

    if codelist.organisation and codelist.organisation not in user.organisations.all():
        # User is collaborator on codelist owned by organisation they don't belong to.
        owner_choices.append(
            (codelist.organisation.owner_identifier, codelist.organisation.name)
        )

    return sorted(owner_choices, key=lambda choice: choice[1])


def handle_get(request, codelist, owner_choices):
    codelist_form = CodelistUpdateForm(
        initial={
            "name": codelist.name,
            "slug": codelist.slug,
            "owner": codelist.owner.owner_identifier,
            "description": codelist.description,
            "methodology": codelist.methodology,
        },
        owner_choices=owner_choices,
    )

    reference_formset = ReferenceFormSet(
        queryset=codelist.references.all(), prefix="reference"
    )
    signoff_formset = SignOffFormSet(queryset=codelist.signoffs.all(), prefix="signoff")

    ctx = {
        "codelist_form": codelist_form,
        "reference_formset": reference_formset,
        "signoff_formset": signoff_formset,
        "owner_choices": owner_choices,
    }
    return TemplateResponse(request, template_name, ctx)


def handle_post(request, codelist, owner_choices):
    codelist_form = CodelistUpdateForm(request.POST, owner_choices=owner_choices)
    reference_formset = ReferenceFormSet(
        request.POST, queryset=codelist.references.all(), prefix="reference"
    )
    signoff_formset = SignOffFormSet(
        request.POST, queryset=codelist.signoffs.all(), prefix="signoff"
    )

    codelist_form.is_valid()

    if (
        codelist_form.is_valid()
        and reference_formset.is_valid()
        and signoff_formset.is_valid()
    ):
        return handle_valid(
            request,
            codelist,
            codelist_form,
            reference_formset,
            signoff_formset,
            owner_choices,
        )
    else:
        return handle_invalid(
            request, codelist_form, reference_formset, signoff_formset, owner_choices
        )


@transaction.atomic
def handle_valid(
    request, codelist, codelist_form, reference_formset, signoff_formset, owner_choices
):
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

    if owner_choices:
        owner = codelist_form.cleaned_data["owner"]
    else:
        owner = codelist.owner

    try:
        actions.update_codelist(
            codelist=codelist,
            owner=owner,
            name=codelist_form.cleaned_data["name"],
            slug=codelist_form.cleaned_data["slug"],
            description=codelist_form.cleaned_data["description"],
            methodology=codelist_form.cleaned_data["methodology"],
            references=references,
            signoffs=signoffs,
        )
    except actions.DuplicateHandleError as e:
        codelist_form.add_error(e.field, f"Duplicate {e.field}")
        return handle_invalid(
            request, codelist_form, reference_formset, signoff_formset, owner_choices
        )

    return redirect(codelist)


def handle_invalid(
    request, codelist_form, reference_formset, signoff_formset, owner_choices
):
    ctx = {
        "codelist_form": codelist_form,
        "reference_formset": reference_formset,
        "signoff_formset": signoff_formset,
        "owner_choices": owner_choices,
    }
    return TemplateResponse(request, template_name, ctx)
