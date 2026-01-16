import csv
from io import StringIO

from django.contrib.auth.decorators import login_required
from django.core.exceptions import NON_FIELD_ERRORS
from django.db.utils import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from codelists import actions as codelist_actions
from codelists.actions import (
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
    descendant_handling = form.cleaned_data.get("descendant_handling")

    print("Descendant handling:", descendant_handling)

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
            if not descendant_handling:
                # User wants to decide on descendants later in the builder so
                # we reset statuses of non-uploaded codes to unresolved
                version = codelist.versions.get()
                # Reset statuses: uploaded codes stay included, everything else becomes unresolved
                version.code_objs.filter(code__in=original_codes).update(status="+")
                version.code_objs.exclude(code__in=original_codes).update(status="?")
                codelist_actions.cache_hierarchy(version=version)
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


def _detect_code_column_header_and_system(rows):
    """Attempt to detect:
     - which column contains clinical codes
     - the coding system
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
      rows: [[row1col1, row1col2, ...], [row2col1, ...], ...],
      uploaded_count: int,
      descendant_count: int,
      missing_descendants_sample: [{code, term}],
      detected_code_column: int (0-based),
      detected_coding_system_id: str or null,
      detected_first_data_row: int (0-based),
      parent_examples: [{
        parent_code: str,
        parent_term: str,
        missing_count: int,
        total_descendants: int,
        display_children: [{type: "item", code: str, term: str, present: bool} | {type: "ellipsis"}]
      }],
      warning: str,
      error: str (optional)
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

    detected_first_data_row = 0
    detected_code_column = 0

    # Detect header row(s)
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

    codes = [
        row[detected_code_column]
        for row in all_rows[detected_first_data_row:]
        if detected_code_column < len(row) and row[detected_code_column].strip()
    ]

    code_set = set(codes)
    # return the first n rows. Always return all the header rows, then at least 3
    # data rows if available. Always return at least 5 rows if available.
    response = {
        "rows": all_rows[: max(detected_first_data_row + 3, 5)],
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

    # Find all parent codes from the CSV that have missing immediate children
    # Only count codes that have at least one immediate child missing
    codes_with_missing_immediate_children = []
    for code in code_set:
        # Get immediate children only
        immediate_children = hierarchy.child_map.get(code, set())
        if not immediate_children:
            continue

        # Find which immediate children are missing from the CSV
        missing_immediate = immediate_children - code_set
        if not missing_immediate:
            continue

        # Check if this code is itself a descendant of another code in the CSV
        # If so, skip it (we only want the highest level)
        # is_child_of_another = False
        # for other_code in code_set:
        #     if other_code != code:
        #         if code in hierarchy.descendants(other_code):
        #             is_child_of_another = True
        #             break

        # if not is_child_of_another:
        num_immediate = len(immediate_children)
        num_missing = len(missing_immediate)
        proportion_missing = num_missing / num_immediate if num_immediate > 0 else 0

        # Priority: codes with 1 immediate child (all missing) get lowest priority
        # Higher proportion of missing children gets higher priority when >=2 children
        if num_immediate == 1:
            sort_key = (0, 0, 0)  # Lowest priority
        else:
            sort_key = (
                1,
                proportion_missing,
                num_immediate,
            )  # Higher priority by proportion

        codes_with_missing_immediate_children.append(
            {
                "code": code,
                "immediate_children": immediate_children,
                "missing_immediate": missing_immediate,
                "sort_key": sort_key,
            }
        )

    # Sort by priority: codes with >=2 children sorted by proportion missing (descending),
    # then codes with 1 child (all at the end)
    codes_with_missing_immediate_children.sort(
        key=lambda x: x["sort_key"], reverse=True
    )

    # Generate examples (up to 3) from the sorted codes
    parent_examples = []
    for item in codes_with_missing_immediate_children[:3]:
        code = item["code"]
        immediate_children = item["immediate_children"]

        # Get terms for parent and all immediate children
        all_codes_to_lookup = [code] + list(immediate_children)
        terms = coding_system.code_to_term(all_codes_to_lookup)

        # Build list of all immediate children with their status
        children_info = []
        for child_code in sorted(immediate_children):
            is_present = child_code in code_set
            has_children = bool(hierarchy.child_map.get(child_code))

            children_info.append(
                {
                    "code": child_code,
                    "term": terms.get(child_code, "[Unknown]"),
                    "present": is_present,
                    "has_children": has_children,
                }
            )

        parent_term = terms.get(code, "[Unknown]")
        parent_examples.append(
            {
                "parent_code": code,
                "parent_term": parent_term,
                "immediate_children": children_info,
            }
        )

    response["descendant_count"] = len(missing_desc)
    response["parent_examples"] = parent_examples
    response["total_parents_with_missing_children"] = len(
        codes_with_missing_immediate_children
    )

    # Build full hierarchy tree for display
    def build_hierarchy_node(code, depth=0):
        """Build a hierarchical node with all its descendants."""
        immediate_children = hierarchy.child_map.get(code, set())
        is_present = code in code_set
        has_children = bool(immediate_children)

        # Check if all descendants are included (for initial collapse state)
        all_descendants_included = True
        if immediate_children:
            descendants_of_code = hierarchy.descendants(code)
            for desc in descendants_of_code:
                if desc not in code_set:
                    all_descendants_included = False
                    break

        node = {
            "id": code,
            "name": coding_system.code_to_term([code]).get(code, "[Unknown]"),
            "status": "+" if is_present else "-",
            "children": [],
            "depth": depth,
            "has_children": has_children,
            "all_descendants_included": all_descendants_included and is_present,
        }

        # Recursively build children
        for child_code in sorted(immediate_children):
            child_node = build_hierarchy_node(child_code, depth + 1)
            node["children"].append(child_node)

        return node

    # Find root codes (codes in CSV that are not descendants of other codes in CSV)
    root_codes = []
    for code in sorted(code_set):
        is_root = True
        for other_code in code_set:
            if other_code != code:
                if code in hierarchy.descendants(other_code):
                    is_root = False
                    break
        if is_root:
            root_codes.append(code)

    # Build hierarchy tree starting from root codes
    full_hierarchy = []
    for root_code in root_codes:
        root_node = build_hierarchy_node(root_code)
        full_hierarchy.append(root_node)

    response["full_hierarchy"] = full_hierarchy

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
    response["total_missing_count"] = len(all_missing_descendants)

    return JsonResponse(response)
