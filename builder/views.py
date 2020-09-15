import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from codelists.hierarchy import Hierarchy
from codelists.presenters import tree_tables
from codelists.search import do_search
from opencodelists.models import User

from . import actions
from .forms import DraftCodelistForm
from .models import DraftCodelist


@login_required
def index(request):
    return redirect("builder:user", request.user.username)


@login_required
def user(request, username):
    user = get_object_or_404(User, username=username)

    if request.method == "POST":
        form = DraftCodelistForm(request.POST)
        if form.is_valid():
            codelist = actions.create_codelist(
                owner=user,
                name=form.cleaned_data["name"],
                coding_system_id=form.cleaned_data["coding_system_id"],
            )
            return redirect(codelist)
    else:
        form = DraftCodelistForm()

    ctx = {
        "user": user,
        "codelists": user.draft_codelists.all().order_by("name"),
        "form": form,
    }
    return render(request, "builder/user.html", ctx)


@login_required
def codelist(request, username, codelist_slug, search_slug=None):
    codelist = get_object_or_404(DraftCodelist, owner=username, slug=codelist_slug)
    coding_system = codelist.coding_system

    code_to_status = dict(codelist.codes.values_list("code", "status"))
    all_codes = list(code_to_status)

    included_codes = [c for c in all_codes if code_to_status[c] == "+"]
    excluded_codes = [c for c in all_codes if code_to_status[c] == "-"]

    if search_slug is None:
        search = None
        displayed_codes = list(code_to_status)
    else:
        search = get_object_or_404(codelist.searches, slug=search_slug)
        displayed_codes = list(search.results.values_list("code__code", flat=True))

    filter = request.GET.get("filter")
    if filter == "included":
        displayed_codes = [c for c in displayed_codes if "+" in code_to_status[c]]
    elif filter == "excluded":
        displayed_codes = [c for c in displayed_codes if "-" in code_to_status[c]]
    elif filter == "unresolved":
        displayed_codes = [c for c in displayed_codes if code_to_status[c] == "?"]
    elif filter == "in-conflict":
        displayed_codes = [c for c in displayed_codes if code_to_status[c] == "!"]
        filter = "in conflict"

    hierarchy = Hierarchy.from_codes(coding_system, all_codes)

    code_to_term = coding_system.code_to_term(all_codes, hierarchy)
    code_to_type = coding_system.code_to_type(all_codes, hierarchy)

    ancestor_codes = hierarchy.filter_to_ultimate_ancestors(set(displayed_codes))
    tables = tree_tables(ancestor_codes, hierarchy, code_to_term, code_to_type)

    searches = [
        {"term": s.term, "url": s.get_absolute_url(), "active": s == search}
        for s in codelist.searches.order_by("term")
    ]
    update_url = reverse(
        "builder:update", args=[codelist.owner.username, codelist.slug]
    )
    search_url = reverse(
        "builder:new_search", args=[codelist.owner.username, codelist.slug]
    )

    ctx = {
        "user": codelist.owner,
        "codelist": codelist,
        "search": search,
        # The following values are passed to the CodelistBuilder component.
        # When any of these chage, use generate_builder_fixture to update
        # static/test/js/fixtures/elbow.json.
        # {
        "searches": searches,
        "filter": filter,
        "tables": tables,
        "included_codes": included_codes,
        "excluded_codes": excluded_codes,
        "displayed_codes": displayed_codes,
        "parent_map": {p: list(cc) for p, cc in hierarchy.parent_map.items()},
        "child_map": {c: list(pp) for c, pp in hierarchy.child_map.items()},
        "is_editable": request.user == codelist.owner,
        "update_url": update_url,
        "search_url": search_url,
        # }
    }

    return render(request, "builder/codelist.html", ctx)


@login_required
@require_http_methods(["POST"])
def update(request, username, codelist_slug):
    codelist = get_object_or_404(DraftCodelist, owner=username, slug=codelist_slug)
    updates = json.loads(request.body)["updates"]
    actions.update_code_statuses(codelist=codelist, updates=updates)
    return JsonResponse({"updates": updates})


@login_required
@require_http_methods(["POST"])
def new_search(request, username, codelist_slug):
    codelist = get_object_or_404(DraftCodelist, owner=username, slug=codelist_slug)
    term = request.POST["term"]
    codes = do_search(codelist.coding_system, term)["all_codes"]
    if not codes:
        # TODO message about no hits
        return redirect(codelist)

    search = actions.create_search(codelist=codelist, term=term, codes=codes)
    return redirect(search)
