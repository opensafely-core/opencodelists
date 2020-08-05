import json
import re
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from codelists import tree_utils
from codelists.search import do_search
from opencodelists.models import User

from . import actions
from .forms import DraftCodelistForm
from .models import DraftCodelist, Search, SearchResult


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
def codelist(request, username, codelist_slug):
    codelist = get_object_or_404(DraftCodelist, owner=username, slug=codelist_slug,)

    if request.method == "POST":
        term = request.POST["term"]
        results = do_search(codelist.coding_system, term)
        if not results["all_codes"]:
            # TODO message about no hits
            return redirect(codelist)

        search = actions.create_search(codelist=codelist, term=term, results=results)
        return redirect(search)

    results = SearchResult.objects.filter(search__codelist=codelist)
    results_context = _results_context(codelist, results)
    tables = _tabulate_subtrees(results_context)
    url = reverse("builder:results", args=[codelist.owner.username, codelist.slug])

    ctx = {
        "codelist": codelist,
        "searches": codelist.searches.all(),
        "results": results,
        "url": url,
        "tables": tables,
        "ancestors_map": results_context["ancestors_map"],
        "descendants_map": results_context["descendants_map"],
        "editable": request.user == codelist.owner,
    }
    return render(request, "builder/codelist.html", ctx)


@login_required
def search(request, username, codelist_slug, search_slug):
    search = get_object_or_404(
        Search.objects.filter(slug=search_slug)
        .prefetch_related("results")
        .select_related("codelist"),
        codelist__owner=username,
        codelist__slug=codelist_slug,
    )
    codelist = search.codelist
    results = search.results.all()
    results_context = _results_context(codelist, results)
    tables = _tabulate_subtrees(results_context)
    url = (
        reverse("builder:results", args=[codelist.owner.username, codelist.slug])
        + f"?term={search.term}"
    )

    ctx = {
        "codelist": codelist,
        "search": search,
        "url": url,
        "tables": tables,
        "ancestors_map": results_context["ancestors_map"],
        "descendants_map": results_context["descendants_map"],
        "editable": request.user == codelist.owner,
    }
    return render(request, "builder/search.html", ctx)


@require_http_methods(["POST"])
def results(request, username, codelist_slug):
    codelist = get_object_or_404(DraftCodelist, owner=username, slug=codelist_slug)

    if "term" in request.GET:
        search = get_object_or_404(codelist.searches, term=request.GET["term"])
        results = SearchResult.objects.filter(search=search)
    else:
        results = SearchResult.objects.filter(search__codelist=codelist)

    updates = json.loads(request.body)["updates"]
    results_context = _results_context(codelist, results)

    actions.update_search(
        results=results,
        updates=updates,
        code_to_status=results_context["code_to_status"],
        ancestors_map=results_context["ancestors_map"],
        descendants_map=results_context["descendants_map"],
    )
    return JsonResponse({"updates": updates})


def _results_context(codelist, results):
    all_codes = [r.code for r in results]
    code_to_term_and_type = {
        code: re.match(r"(^.*) \(([\w/ ]+)\)$", term).groups()
        for code, term in codelist.coding_system.lookup_names(all_codes).items()
    }
    code_to_term = {code: term for code, (term, _) in code_to_term_and_type.items()}
    code_to_type = {code: typ_ for code, (_, typ_) in code_to_term_and_type.items()}
    code_to_status = {result.code: result.status for result in results}

    ancestor_codes = [r.code for r in results if r.is_ancestor]
    subtrees = tree_utils.build_descendant_subtrees(
        codelist.coding_system, ancestor_codes
    )

    subtrees_by_type = defaultdict(list)
    for code, subtree in zip(ancestor_codes, subtrees):
        typ_ = code_to_type[code]
        subtrees_by_type[typ_].append(subtree)

    descendants_map = {}
    for subtree in subtrees:
        descendants_map.update(tree_utils.build_descendants_map(subtree))
    descendants_map = {
        ancestor: list(descendants) for ancestor, descendants in descendants_map.items()
    }

    ancestors_map = {code: set() for code in all_codes}
    for ancestor, descendants in descendants_map.items():
        for descendant in descendants:
            ancestors_map[descendant].add(ancestor)
    ancestors_map = {
        descendant: list(ancestors) for descendant, ancestors in ancestors_map.items()
    }

    return {
        "code_to_term": code_to_term,
        "code_to_type": code_to_type,
        "code_to_status": code_to_status,
        "subtrees_by_type": subtrees_by_type,
        "descendants_map": descendants_map,
        "ancestors_map": ancestors_map,
    }


def _tabulate_subtrees(results_context):
    code_to_status = results_context["code_to_status"]
    code_to_term = results_context["code_to_term"]
    sort_key = code_to_term.__getitem__
    tables = []

    for typ_ in sorted(results_context["subtrees_by_type"]):
        subtrees = results_context["subtrees_by_type"][typ_]
        depth = -1
        rows = []

        for subtree in sorted(subtrees, key=lambda st: code_to_term[list(st)[0]]):
            for code, direction in tree_utils.walk_tree_depth_first(subtree, sort_key):
                depth += direction
                if direction == 1:
                    rows.append(
                        {
                            "indent": (depth + 1) * 1.5,
                            "code": code,
                            "status": code_to_status[code],
                            "term": code_to_term[code],
                        }
                    )

        table = {
            "heading": typ_.title(),
            "rows": rows,
        }
        tables.append(table)
    return tables
