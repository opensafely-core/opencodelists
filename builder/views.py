import json
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods

from codelists.models import Search
from codelists.search import do_search

from . import actions
from .decorators import load_draft, require_permission

NO_SEARCH_TERM = object()


@load_draft
def draft(request, draft):
    return _draft(request, draft, None)


@load_draft
def search(request, draft, search_slug):
    return _draft(request, draft, search_slug)


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


def _draft(request, draft, search_slug):
    if request.method == "POST":
        return _handle_post(request, draft)

    codelist = draft.codelist
    coding_system = draft.coding_system
    codeset = draft.codeset
    hierarchy = codeset.hierarchy

    if search_slug is None:
        search = None
        displayed_codes = list(codeset.all_codes())
    elif search_slug is NO_SEARCH_TERM:
        search = NO_SEARCH_TERM
        displayed_codes = list(
            draft.code_objs.filter(results=None).values_list("code", flat=True)
        )
    else:
        search = get_object_or_404(draft.searches, slug=search_slug)
        displayed_codes = list(search.results.values_list("code_obj__code", flat=True))

    searches = [
        {
            "term_or_code": s.term_or_code,
            "url": draft.get_builder_search_url(s.slug),
            "delete_url": draft.get_builder_delete_search_url(s.slug),
            "active": s == search,
        }
        for s in draft.searches.order_by("term")
    ]

    if searches and draft.code_objs.filter(results=None).exists():
        searches.append(
            {
                "term_or_code": "[no search term]",
                "url": draft.get_builder_no_search_term_url(),
                "active": search_slug == NO_SEARCH_TERM,
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

    if search_slug == NO_SEARCH_TERM:
        results_heading = "Showing concepts with no matching search term"
    elif search_slug is not None:
        results_heading = f'Showing concepts matching "{search.term_or_code}"'
    elif codeset.all_codes():
        results_heading = "Showing all matching concepts"
    else:
        results_heading = (
            "Start building your codelist by searching for a term or a code"
        )

    draft_url = draft.get_builder_draft_url()
    update_url = draft.get_builder_update_url()
    search_url = draft.get_builder_new_search_url()

    versions = [
        {
            "tag_or_hash": v.tag_or_hash,
            "url": v.get_absolute_url(),
            "status": v.status,
            "current": v == draft,
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
    metadata = {
        "coding_system_name": draft.coding_system.name,
        "coding_system_release": {
            "release_name": draft.coding_system_release.release_name,
            "valid_from": coding_system_valid_from_date,
        },
        "organisation_name": codelist.organisation.name
        if codelist.organisation
        else None,
        "codelist_full_slug": codelist.full_slug(),
        "hash": draft.hash,
    }

    ctx = {
        "user": draft.author,
        "draft": draft,
        "codelist_name": codelist.name,
        # The following values are passed to the CodelistBuilder component.
        # When any of these chage, use generate_builder_fixture to update
        # static/test/js/fixtures/elbow.json.
        # {
        "results_heading": results_heading,
        "searches": searches,
        "filter": filter,
        "tree_tables": tree_tables,
        "all_codes": list(codeset.all_codes()),
        "included_codes": list(codeset.codes("+")),
        "excluded_codes": list(codeset.codes("-")),
        "parent_map": {p: list(cc) for p, cc in hierarchy.parent_map.items()},
        "child_map": {c: list(pp) for c, pp in hierarchy.child_map.items()},
        "code_to_term": code_to_term,
        "code_to_status": codeset.code_to_status,
        "is_editable": request.user == draft.author,
        "draft_url": draft_url,
        "update_url": update_url,
        "search_url": search_url,
        "versions": versions,
        "metadata": metadata,
    }

    return render(request, "builder/draft.html", ctx)


@login_required
@require_http_methods(["POST"])
@load_draft
@require_permission
def update(request, draft):
    updates = json.loads(request.body)["updates"]
    actions.update_code_statuses(draft=draft, updates=updates)
    return JsonResponse({"updates": updates})


@login_required
@require_http_methods(["POST"])
@load_draft
@require_permission
def new_search(request, draft):
    term = request.POST["search"].strip()
    # Ensure that the term is not an empty string after slugifying
    # (e.g. if the user entered "*" as a search term)
    if not slugify(term):
        messages.info(request, f'"{term}" is not a valid search term')
        return redirect(draft.get_builder_draft_url())
    if term.startswith("code:"):
        code = term[5:].strip()
        term = None
    else:
        code = None

    codes = do_search(draft.coding_system, term=term, code=code)["all_codes"]

    search = actions.create_search(draft=draft, term=term, code=code, codes=codes)

    if not codes:
        messages.info(request, f'There are no results for "{code or term}"')

    return redirect(draft.get_builder_search_url(search.slug))


@login_required
@require_http_methods(["POST"])
@load_draft
@require_permission
def delete_search(request, draft, search_slug):
    search = get_object_or_404(Search, version=draft, slug=search_slug)
    actions.delete_search(search=search)
    messages.info(
        request,
        f'Search for "{search_slug}" deleted. Any codes matching "{search_slug}" that '
        "do not match any other search term and which are not included in the codelist have been removed",
    )
    return redirect(draft.get_builder_draft_url())
