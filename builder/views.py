import json
import re

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

    if search_slug is None:
        search = None
        codes_for_display = code_to_status
    else:
        search = get_object_or_404(codelist.searches, slug=search_slug)
        codes_for_display = search.results.values_list("code__code", flat=True)

    filter = request.GET.get("filter")
    if filter == "included":
        codes_for_display = {c for c in codes_for_display if "+" in code_to_status[c]}
    elif filter == "excluded":
        codes_for_display = {c for c in codes_for_display if "-" in code_to_status[c]}
    elif filter == "unresolved":
        codes_for_display = {c for c in codes_for_display if code_to_status[c] == "?"}
    elif filter == "in-conflict":
        codes_for_display = {c for c in codes_for_display if code_to_status[c] == "!"}
        filter = "in conflict"
    else:
        codes_for_display = set(codes_for_display)

    code_to_term_and_type = {
        code: re.match(r"(^.*) \(([\w/ ]+)\)$", term).groups()
        for code, term in coding_system.lookup_names(all_codes).items()
    }
    code_to_term = {code: term for code, (term, _) in code_to_term_and_type.items()}
    code_to_type = {code: type for code, (_, type) in code_to_term_and_type.items()}

    hierarchy = Hierarchy.from_codes(coding_system, all_codes)

    ancestor_codes = hierarchy.filter_to_ultimate_ancestors(codes_for_display)
    tables = tree_tables(
        ancestor_codes, hierarchy, code_to_term, code_to_type, code_to_status
    )

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
        "searches": searches,
        "filter": filter,
        "code_to_status": code_to_status,
        "tables": tables,
        "parent_map": {p: list(cc) for p, cc in hierarchy.parent_map.items()},
        "child_map": {c: list(pp) for c, pp in hierarchy.child_map.items()},
        "is_editable": request.user == codelist.owner,
        "update_url": update_url,
        "search_url": search_url,
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
