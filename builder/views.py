import json
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import linebreaks
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods

from codelists.actions import update_codelist
from codelists.forms import CodelistUpdateForm
from codelists.models import Search
from codelists.search import do_search
from opencodelists.templatetags.markdown_filter import render_markdown

from . import actions
from .decorators import load_draft, require_permission


NO_SEARCH_TERM = object()


@load_draft
def draft(request, draft):
    return _draft(request, draft, None)


@load_draft
def search(request, draft, search_id, search_slug):
    return _draft(request, draft, search_id)


@load_draft
def no_search_term(request, draft):
    return _draft(request, draft, NO_SEARCH_TERM)


@login_required
@require_permission
def _handle_post(request, draft):
    action = request.POST["action"]
    if action == "save-for-review":
        actions.save(draft=draft)
        messages.add_message(
            request, messages.INFO, "A new version has been saved for review"
        )
        return redirect(draft)
    elif action == "save-draft":
        messages.add_message(request, messages.INFO, "Your changes have been saved")
        return redirect(draft.codelist)
    elif action == "discard":
        messages.add_message(request, messages.INFO, "Your changes have been discarded")
        actions.discard_draft(draft=draft)
        # check if the discarded draft's codelist still exists (i.e. this was not the only version)
        if draft.codelist.id is not None:
            return redirect(draft.codelist)
        return redirect(reverse("user", args=(request.user.username,)))
    else:
        return HttpResponse(status=400)


def _get_help_text(codelist):
    """Get the help_text for fields from the form"""
    # Create form instance - we pass the current methodology
    # because the help text may change based on its value
    form_data = {"methodology": codelist.methodology}
    form = CodelistUpdateForm(initial=form_data, owner_choices=[])

    # Get the help_text attribute from the description and methodology fields
    return form.fields["description"].help_text, form.fields["methodology"].help_text


def _get_description_max_length(codelist):
    """Get the max_length for description field from the form"""
    # Create form instance with current description
    form_data = {"description": codelist.description}
    form = CodelistUpdateForm(initial=form_data, owner_choices=[])

    # Get the max_length attribute from the description field widget
    return form.fields["description"].widget.attrs.get("maxlength")


def _draft(request, draft, search_id):
    if request.method == "POST":
        return _handle_post(request, draft)

    codelist = draft.codelist
    coding_system = draft.coding_system
    codeset = draft.codeset
    hierarchy = codeset.hierarchy

    if search_id is None:
        search = None
        displayed_codes = list(codeset.all_codes())
    elif search_id is NO_SEARCH_TERM:
        search = NO_SEARCH_TERM
        displayed_codes = list(
            draft.code_objs.filter(results=None).values_list("code", flat=True)
        )
    else:
        search = get_object_or_404(draft.searches, id=search_id)
        displayed_codes = list(search.results.values_list("code_obj__code", flat=True))

    searches = [
        {
            "term_or_code": s.term_or_code,
            "url": draft.get_builder_search_url(s.id, s.slug),
            "delete_url": draft.get_builder_delete_search_url(s.id, s.slug),
            "active": s == search,
        }
        for s in draft.searches.order_by("term")
    ]

    if draft.code_objs.filter(results=None).exists():
        searches.append(
            {
                "term_or_code": "[no search term]",
                "url": draft.get_builder_no_search_term_url(),
                "active": search_id == NO_SEARCH_TERM,
            }
        )

    filter = request.GET.get("filter")
    if filter == "in-conflict":
        filter = "in conflict"

    if filter:
        statuses = {
            "included": ["+", "(+)"],
            "excluded": ["-", "(-)"],
            "unresolved": ["?"],
            "in conflict": ["!"],
        }[filter]
        codes_with_status = codeset.codes(statuses)
        displayed_codes = [c for c in displayed_codes if c in codes_with_status]

    ancestor_codes = hierarchy.filter_to_ultimate_ancestors(set(displayed_codes))
    code_to_term = coding_system.code_to_term(codeset.all_codes())
    tree_tables = sorted(
        (type, sorted(codes, key=code_to_term.__getitem__))
        for type, codes in coding_system.codes_by_type(
            ancestor_codes, hierarchy
        ).items()
    )

    num_displayed_codes = len(displayed_codes)
    if search_id:
        # A search term has been selected OR there are codes orphaned from their search
        # term. In either case this is not an empty codelist
        is_empty_codelist = False
        heading_prefix = f"Showing {num_displayed_codes} concept{'s' if num_displayed_codes != 1 else ''}"
        if search_id == NO_SEARCH_TERM:
            results_heading = f"{heading_prefix} with no matching search term"
        elif search.term:
            results_heading = f'{heading_prefix} matching "{search.term}"'
        else:
            results_heading = f"{heading_prefix} matching the code: {search.code}"
    elif codeset.all_codes():
        # No search term selected, but we have >0 codes, so this is not an empty codelist
        is_empty_codelist = False
        results_heading = (
            f"Showing all {filter or 'matching'} concepts ({num_displayed_codes})"
        )
    elif searches:
        # No search term selected and there are no codes, but there are >0 searches
        is_empty_codelist = False
        results_heading = "None of your searches match any concepts"
    else:
        # No codes or searches
        is_empty_codelist = True
        # No need to provide a value for the results_heading as this is no longer
        # used for an empty codelist. We need to give it a value though to prevent
        # errors
        results_heading = ""

    draft_url = draft.get_builder_draft_url()
    update_url = draft.get_builder_update_url()
    search_url = draft.get_builder_new_search_url()

    versions = [
        {
            "tag_or_hash": v.tag_or_hash,
            "url": v.get_absolute_url(),
            "status": v.status,
            "current": v == draft,
            "created_at": v.created_at,
        }
        for v in codelist.visible_versions(request.user)
    ]

    # Each coding system release has a "valid_from" date.  For codelist versions imported
    # before releases were tracked, the exact coding_system_release they were created with
    # can't be confirmed, so it is set to a default CSR with release_name "unknown" and
    # valid_from floor date 1900-01-01.  If the CSR is the default "unknown" one, we don't
    # display the valid_from date to the user
    coding_system_valid_from_date = (
        draft.coding_system_release.valid_from.strftime("%Y-%m-%d")
        if draft.coding_system_release.valid_from > date(1900, 1, 1)
        else None
    )
    description_help_text, methodology_help_text = _get_help_text(codelist)
    metadata = {
        "coding_system_id": draft.coding_system.id,
        "coding_system_name": draft.coding_system.name,
        "coding_system_release": {
            "release_name": draft.coding_system_release.release_name,
            "valid_from": coding_system_valid_from_date,
        },
        "organisation_name": (
            codelist.organisation.name if codelist.organisation else None
        ),
        "codelist_full_slug": codelist.full_slug(),
        "hash": draft.hash,
        "codelist_name": codelist.name,
        "description": {
            "text": codelist.description,
            "html": linebreaks(codelist.description),
            "help_text": description_help_text,
            "max_length": _get_description_max_length(codelist),
        },
        "methodology": {
            "text": codelist.methodology,
            "html": render_markdown(codelist.methodology),
            "help_text": methodology_help_text,
        },
        "references": [
            {"text": r.text, "url": r.url} for r in codelist.references.all()
        ],
    }

    ctx = {
        "user": draft.author,
        "draft": draft,
        "codelist_name": codelist.name,
        # The following values are passed to the CodelistBuilder component.
        # When any of these change, use generate_builder_fixture to update
        # static/test/js/fixtures/elbow.json.
        # {
        "results_heading": results_heading,
        "searches": searches,
        "tree_tables": tree_tables,
        "all_codes": list(codeset.all_codes()),
        "parent_map": {p: list(cc) for p, cc in hierarchy.parent_map.items()},
        "child_map": {c: list(pp) for c, pp in hierarchy.child_map.items()},
        "code_to_term": code_to_term,
        "code_to_status": codeset.code_to_status,
        "is_editable": request.user == draft.author,
        "draft_url": draft_url,
        "update_url": update_url,
        "search_url": search_url,
        "sort_by_term": coding_system.sort_by_term,
        "versions": versions,
        "metadata": metadata,
        "is_empty_codelist": is_empty_codelist,
    }

    return render(request, "builder/draft.html", ctx)


@login_required
@require_http_methods(["POST"])
@load_draft
@require_permission
def update(request, draft):
    json_body = json.loads(request.body)

    # If the status of any codes (include/exclude) has changed then
    # this is passed in the "updates" field
    updates = []
    if "updates" in json_body:
        updates = json.loads(request.body)["updates"]
        actions.update_code_statuses(draft=draft, updates=updates)

    # It's also possible to update the description and methodology of
    # the codelist metadata.
    updated_fields = {
        "owner": draft.codelist.owner,
        "name": draft.codelist.name,
        "slug": draft.codelist.slug,
        "description": draft.codelist.description,
        "methodology": draft.codelist.methodology,
        "references": [
            {"url": reference.url, "text": reference.text}
            for reference in draft.codelist.references.all()
        ],
        "signoffs": [
            {"user": signoff.user, "date": signoff.date}
            for signoff in draft.codelist.signoffs.all()
        ],
    }
    metadata_updated = False
    for field in ["description", "methodology", "references"]:
        if field in json_body:
            updated_fields[field] = json_body[field]
            metadata_updated = True

    response = {"updates": updates}
    if metadata_updated:
        update_codelist(codelist=draft.codelist, **updated_fields)
        description_help_text, methodology_help_text = _get_help_text(draft.codelist)
        response["metadata"] = {
            "description": {
                "text": updated_fields["description"],
                "html": linebreaks(updated_fields["description"]),
                "help_text": description_help_text,
                "max_length": _get_description_max_length(draft.codelist),
            },
            "methodology": {
                "text": updated_fields["methodology"],
                "html": render_markdown(updated_fields["methodology"]),
                "help_text": methodology_help_text,
            },
            "references": updated_fields["references"],
        }

    return JsonResponse(response)


@login_required
@require_http_methods(["POST"])
@load_draft
@require_permission
def new_search(request, draft):
    term = request.POST["search"].strip()
    search_type = request.POST["search-type"]
    # Ensure that the term is not an empty string after slugifying
    # (e.g. if the user entered "*" as a search term)
    if not slugify(term):
        messages.error(request, f'"{term}" is not a valid search term')
        return redirect(draft.get_builder_draft_url())
    if search_type == "code":
        code = term
        term = None
    else:
        code = None

    # Create temporary model instance to validate the term and code fields to
    # ensure e.g. that max_length constraints are enforced
    search = draft.searches.model(term=term, code=code)
    try:
        search.clean_fields(exclude=["slug", "version"])  # validate only term and code
    except ValidationError as e:
        for field, errors in e.message_dict.items():
            messages.error(request, f"{field}: {', '.join(errors)}")
        return redirect(draft.get_builder_draft_url())

    codes = do_search(draft.coding_system, term=term, code=code)["all_codes"]

    search = actions.create_search(draft=draft, term=term, code=code, codes=codes)

    if isinstance(search, dict) and search.get("error"):
        messages.error(request, search["message"])
        return redirect(draft.get_builder_draft_url())

    return redirect(draft.get_builder_search_url(search.id, search.slug))


@login_required
@require_http_methods(["POST"])
@load_draft
@require_permission
def delete_search(request, draft, search_id, search_slug):
    search = get_object_or_404(Search, version=draft, id=search_id)
    actions.delete_search(search=search)
    messages.info(
        request,
        f'Search for "{search_slug}" deleted. Any codes matching "{search_slug}" that '
        "do not match any other search term and which are not included in the codelist have been removed",
    )
    return redirect(draft.get_builder_draft_url())
