import csv
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from codelists.hierarchy import Hierarchy
from codelists.search import do_search
from mappings.bnfdmd.mappers import bnf_to_dmd
from opencodelists.models import User

from . import actions
from .decorators import load_codelist
from .forms import DraftCodelistForm

NO_SEARCH_TERM = object()


@load_codelist
def download(request, codelist):
    # get codes
    codes = list(
        codelist.codes.filter(status__contains="+").values_list("code", flat=True)
    )

    # get terms for codes
    code_to_term = codelist.coding_system.lookup_names(codes)

    timestamp = timezone.now().strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"{codelist.owner.username}-{codelist.slug}-{timestamp}.csv"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    # render to csv
    writer = csv.writer(response)
    writer.writerow(["id", "term"])
    writer.writerows([(k, v) for k, v in code_to_term.items()])

    return response


@load_codelist
def download_dmd(request, codelist):
    if codelist.coding_system_id != "bnf":
        raise "Http404"

    # get codes
    codes = list(
        codelist.codes.filter(status__contains="+").values_list("code", flat=True)
    )

    timestamp = timezone.now().strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"{codelist.owner.username}-{codelist.slug}-{timestamp}.csv"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    dmd_rows = bnf_to_dmd(codes)
    writer = csv.DictWriter(response, ["dmd_type", "dmd_id", "dmd_name", "bnf_code"])
    writer.writeheader()
    writer.writerows(dmd_rows)

    return response


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


@load_codelist
def codelist(request, draft):
    return _codelist(request, draft, None)


@login_required
@load_codelist
def search(request, draft, search_slug):
    return _codelist(request, draft, search_slug)


@login_required
@load_codelist
def no_search_term(request, draft):
    return _codelist(request, draft, NO_SEARCH_TERM)


def _codelist(request, codelist, search_slug):
    coding_system = codelist.coding_system

    code_to_status = dict(codelist.codes.values_list("code", "status"))
    all_codes = list(code_to_status)

    included_codes = [c for c in all_codes if code_to_status[c] == "+"]
    excluded_codes = [c for c in all_codes if code_to_status[c] == "-"]

    if search_slug is None:
        search = None
        displayed_codes = list(code_to_status)
    elif search_slug is NO_SEARCH_TERM:
        search = NO_SEARCH_TERM
        displayed_codes = list(
            codelist.codes.filter(results=None).values_list("code", flat=True)
        )
    else:
        search = get_object_or_404(codelist.searches, slug=search_slug)
        displayed_codes = list(search.results.values_list("code__code", flat=True))

    searches = [
        {"term": s.term, "url": s.get_absolute_url(), "active": s == search}
        for s in codelist.searches.order_by("term")
    ]

    if searches and codelist.codes.filter(results=None).exists():
        searches.append(
            {
                "term": "[no search term]",
                "url": reverse(
                    "builder:no-search-term",
                    args=[codelist.owner.username, codelist.slug],
                ),
                "active": search_slug == NO_SEARCH_TERM,
            }
        )

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

    ancestor_codes = hierarchy.filter_to_ultimate_ancestors(set(displayed_codes))
    code_to_term = coding_system.code_to_term(hierarchy.nodes | set(all_codes))
    tree_tables = sorted(
        (type.title(), sorted(codes, key=code_to_term.__getitem__))
        for type, codes in coding_system.codes_by_type(
            ancestor_codes, hierarchy
        ).items()
    )

    update_url = reverse(
        "builder:update", args=[codelist.owner.username, codelist.slug]
    )
    search_url = reverse(
        "builder:new_search", args=[codelist.owner.username, codelist.slug]
    )
    download_url = reverse(
        "builder:download", args=[codelist.owner.username, codelist.slug]
    )

    if codelist.coding_system_id == "bnf":
        download_dmd_url = reverse(
            "builder:download-dmd", args=[codelist.owner.username, codelist.slug]
        )
    else:
        download_dmd_url = None

    ctx = {
        "user": codelist.owner,
        "codelist": codelist,
        "search": search,
        "NO_SEARCH_TERM": NO_SEARCH_TERM,
        # The following values are passed to the CodelistBuilder component.
        # When any of these chage, use generate_builder_fixture to update
        # static/test/js/fixtures/elbow.json.
        # {
        "searches": searches,
        "filter": filter,
        "tree_tables": tree_tables,
        "all_codes": all_codes,
        "included_codes": included_codes,
        "excluded_codes": excluded_codes,
        "parent_map": {p: list(cc) for p, cc in hierarchy.parent_map.items()},
        "child_map": {c: list(pp) for c, pp in hierarchy.child_map.items()},
        "code_to_term": code_to_term,
        "code_to_status": code_to_status,
        "is_editable": request.user == codelist.owner,
        "update_url": update_url,
        "search_url": search_url,
        "download_url": download_url,
        "download_dmd_url": download_dmd_url,
        # }
    }

    return render(request, "builder/codelist.html", ctx)


@login_required
@require_http_methods(["POST"])
@load_codelist
def update(request, codelist):
    updates = json.loads(request.body)["updates"]
    actions.update_code_statuses(codelist=codelist, updates=updates)
    return JsonResponse({"updates": updates})


@login_required
@require_http_methods(["POST"])
@load_codelist
def new_search(request, codelist):
    term = request.POST["term"]
    codes = do_search(codelist.coding_system, term)["all_codes"]
    if not codes:
        # TODO message about no hits
        return redirect(codelist)

    search = actions.create_search(codelist=codelist, term=term, codes=codes)
    return redirect(search)
