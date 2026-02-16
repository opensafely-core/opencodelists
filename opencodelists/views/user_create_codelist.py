import csv
from io import StringIO

from django.contrib.auth.decorators import login_required
from django.core.exceptions import NON_FIELD_ERRORS
from django.db.utils import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from codelists.actions import (
    cache_hierarchy,
    create_codelist_from_scratch,
    create_codelist_with_codes,
)
from codelists.coding_systems import (
    CODING_SYSTEMS,
    builder_compatible_coding_systems,
    most_recent_database_alias,
)
from codelists.hierarchy import Hierarchy
from opencodelists.forms import validate_csv_data_codes

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
    original_codes = list(codes) if codes else []
    exclude_child_codes = form.cleaned_data.get("exclude_child_codes")

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
            if not exclude_child_codes:
                # User wants to decide on descendants later in the builder so
                # we reset statuses of non-uploaded codes to unresolved
                version = codelist.versions.get()
                # Reset statuses: uploaded codes stay included, everything else becomes unresolved
                version.code_objs.filter(code__in=original_codes).update(status="+")
                version.code_objs.exclude(code__in=original_codes).update(status="?")
                cache_hierarchy(version=version)
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


@login_required
@require_POST
def csv_descendants_preview(request, username):
    """Parse an uploaded CSV and report descendants not included.

    Auto-detects: first data row, code column, and coding system.

    Returns JSON: {
      rows_preview: [[row1col1, row1col2, ...], [row2col1, ...], ...],  - first 5 rows of the CSV for preview
      uploaded_count: int,                                              - number of unique codes uploaded
      detected_first_data_row: int (0-based),                           - index of first data row
      detected_code_column: int (0-based),                              - index of column with clinical codes
      detected_coding_system_id: str or null,                           - detected coding system ID
      missing_descendants: [{code, term}],                              - list of missing descendant codes with terms (descriptions)
      error: str,                                                       - error message if applicable
      warning: str                                                      - warning message if applicable
    }
    """

    user = get_object_or_404(User, username=username)
    if user != request.user:
        return JsonResponse({"error": "Not allowed"}, status=403)

    csv_file = request.FILES.get("csv_data")
    coding_system_id = request.POST.get("coding_system_id")

    if not csv_file:
        return JsonResponse({"error": "csv_data required"}, status=400)

    try:
        data = csv_file.read().decode("utf-8-sig")
    except UnicodeDecodeError as e:
        return JsonResponse({"error": f"Failed to read CSV: {e}"}, status=400)

    # Parse all rows to support auto-detection
    all_rows = list(csv.reader(StringIO(data)))
    if not all_rows:
        return JsonResponse({"error": "CSV is empty"}, status=400)

    detected_first_data_row, detected_code_column, detected_coding_system_id = (
        _detect_code_column_header_and_system(all_rows)
    )

    if not detected_coding_system_id:
        return JsonResponse(
            {
                "error": "No coding system could be detected in the CSV - are you sure it contains valid codes?"
            },
            status=400,
        )
    elif coding_system_id and detected_coding_system_id != coding_system_id:
        return JsonResponse(
            {
                "error": f"Detected coding system ({detected_coding_system_id}) does not match specified coding system ({coding_system_id})."
            },
            status=400,
        )

    # Extract codes from detected column skipping header rows
    codes = [
        row[detected_code_column]
        for row in all_rows[detected_first_data_row:]
        if detected_code_column < len(row) and row[detected_code_column].strip()
    ]

    code_set = set(codes)

    response = {
        "rows_preview": all_rows[: max(detected_first_data_row + 3, 5)],
        "uploaded_count": len(code_set),
        "detected_first_data_row": detected_first_data_row,
        "detected_code_column": detected_code_column,
        "detected_coding_system_id": detected_coding_system_id,
    }

    # Validate codes
    coding_system = CODING_SYSTEMS[
        detected_coding_system_id
    ].get_by_release_or_most_recent()
    try:
        validate_csv_data_codes(coding_system, codes)
    except Exception as e:
        response["warning"] = e.message
        return JsonResponse(response)

    # Compute descendants not included
    hierarchy = Hierarchy.from_codes(coding_system, code_set)
    missing_desc = set()
    for code in code_set:
        missing_desc |= hierarchy.descendants(code)
    missing_desc -= code_set

    # Collect all missing descendants with their terms
    all_missing_descendants = []
    for code in sorted(missing_desc):
        all_missing_descendants.append(
            {
                "code": code,
                "term": coding_system.lookup_names([code])[code],
            }
        )

    response["all_missing_descendants"] = all_missing_descendants

    return JsonResponse(response)
