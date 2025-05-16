from django.contrib.auth.decorators import login_required
from django.core.exceptions import NON_FIELD_ERRORS
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from codelists.actions import create_codelist_from_scratch, create_codelist_with_codes
from codelists.coding_systems import CODING_SYSTEMS, most_recent_database_alias
from coding_systems.base.coding_system_base import BuilderCompatibleCodingSystem

from ..forms import CodelistCreateForm
from ..models import Organisation, User


@login_required
def user_create_codelist(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        return redirect("/")

    if user.organisations.exists():
        owner_choices = [(f"user:{user.pk}", "Me")]
        for organisation in user.organisations.order_by("name"):
            owner_choices.append((f"organisation:{organisation.pk}", organisation.name))
    else:
        owner_choices = []

    if request.method == "POST":
        return handle_post(request, user, owner_choices)
    return handle_get(request, user, owner_choices)


def handle_get(request, user, owner_choices):
    coding_systems = sorted(
        [
            {"name": system.name, "description": system.description}
            for id, system in CODING_SYSTEMS.items()
            if issubclass(system, BuilderCompatibleCodingSystem)
        ],
        key=lambda x: x["name"].lower(),
    )
    ctx = {
        "user": user,
        "form": CodelistCreateForm(owner_choices=owner_choices),
        "coding_systems": coding_systems,
    }
    return render(request, "opencodelists/user_create_codelist.html", ctx)


def handle_post(request, user, owner_choices):
    form = CodelistCreateForm(request.POST, request.FILES, owner_choices=owner_choices)

    if form.is_valid():
        return handle_post_valid(request, form, user, owner_choices)
    else:
        return handle_post_invalid(request, form, user)


def handle_post_valid(request, form, user, owner_choices):
    if owner_choices:
        # TODO handle these asserts better
        owner_identifier = form.cleaned_data["owner"]
        assert owner_identifier in [choice[0] for choice in owner_choices]
        if owner_identifier.startswith("user:"):
            owner = get_object_or_404(User, username=owner_identifier[5:])
            assert owner == user
        else:
            assert owner_identifier.startswith("organisation:")
            owner = get_object_or_404(Organisation, slug=owner_identifier[13:])
            assert user.is_member(owner)
    else:
        owner = user

    name = form.cleaned_data["name"]
    coding_system_id = form.cleaned_data["coding_system_id"]
    codes = form.cleaned_data["csv_data"]

    # TODO: Retrieve coding system database alias from form input when
    # coding system version is selectable
    coding_system_database_alias = most_recent_database_alias(coding_system_id)

    try:
        if codes:
            codelist = create_codelist_with_codes(
                owner=owner,
                name=name,
                coding_system_id=coding_system_id,
                codes=codes,
                coding_system_database_alias=coding_system_database_alias,
                author=user,
            )
        else:
            codelist = create_codelist_from_scratch(
                owner=owner,
                name=name,
                coding_system_id=coding_system_id,
                coding_system_database_alias=coding_system_database_alias,
                author=user,
            )
    except IntegrityError as e:
        assert "UNIQUE constraint failed" in str(e)
        form.add_error(
            NON_FIELD_ERRORS,
            f"There is already a codelist called {name}",
        )
        return handle_post_invalid(request, form, user)

    return redirect(codelist.versions.get())


def handle_post_invalid(request, form, user):
    ctx = {"user": user, "form": form}
    return render(request, "opencodelists/user_create_codelist.html", ctx)
