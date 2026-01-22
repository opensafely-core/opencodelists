from django.contrib.auth.decorators import login_required
from django.core.exceptions import NON_FIELD_ERRORS
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from codelists.actions import (
    create_codelist_from_scratch,
    create_codelist_with_codes,
)
from codelists.coding_systems import (
    CODING_SYSTEMS,
    builder_compatible_coding_systems,
    most_recent_database_alias,
)

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

    # We allow people to view hidden coding systems if we want user feedback before rolling out
    # It can be access via /users/<username>/new-codelist/?include_experimental_coding_systems
    include_experimental = "include_experimental_coding_systems" in request.GET

    if request.method == "POST":
        return handle_post(request, user, owner_choices, include_experimental)
    return handle_get(request, user, owner_choices, include_experimental)


def handle_get(request, user, owner_choices, include_experimental):
    coding_systems = [
        {
            "name": system.name,
            "description": system.description,
            "is_experimental": system.is_experimental,
        }
        for system in builder_compatible_coding_systems(
            include_experimental=include_experimental
        )
    ]

    ctx = {
        "user": user,
        "form": CodelistCreateForm(
            owner_choices=owner_choices, include_experimental=include_experimental
        ),
        "coding_systems": coding_systems,
    }
    return render(request, "opencodelists/user_create_codelist.html", ctx)


def handle_post(request, user, owner_choices, include_experimental):
    form = CodelistCreateForm(
        request.POST,
        request.FILES,
        owner_choices=owner_choices,
        include_experimental=include_experimental,
    )

    if form.is_valid():
        return handle_post_valid(request, form, user, owner_choices)
    else:
        return handle_post_invalid(request, form, user)


def handle_post_valid(request, form, user, owner_choices):
    if owner_choices:
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


def _detect_code_column_header_and_system(rows: list[list[str]]):
    """
    Input: rows from a CSV file as list of lists of strings.

    Purpose: Attempt to detect:
      - which column contains clinical codes
      - the clinical coding system
      - which row is the first data row (everything before is header)

    Returns: (first_data_row_idx, code_column_idx, detected_system_id) or (0, 0, None) if detection fails.
    """
    if not rows or len(rows) < 1:
        return 0, 0, None

    # Try each column
    for col_idx in range(len(rows[0])):
        sample_codes = [
            row[col_idx] for row in rows[: min(10, len(rows))] if col_idx < len(row)
        ]

        if not sample_codes:
            continue

        # Try each coding system to see if it recognizes these codes
        for cs_id, cs_class in CODING_SYSTEMS.items():
            if not cs_class.is_builder_compatible():
                continue
            try:
                cs = cs_class.get_by_release_or_most_recent()
                if not cs.has_database:
                    continue
                # Check if any codes validate
                valid = set(sample_codes) & set(cs.lookup_names(sample_codes))

                # If any valid we, first find the first row with a valid code
                # then see if enough codes are valid to consider this a match
                if not valid:
                    continue

                for first_valid_code_idx, code in enumerate(sample_codes):
                    if code in valid:
                        break

                if len(valid) >= max(
                    1, (len(sample_codes[first_valid_code_idx:]) * 8) // 10
                ):  # >80% match
                    return first_valid_code_idx, col_idx, cs_id

            except Exception:
                continue

    return 0, 0, None
