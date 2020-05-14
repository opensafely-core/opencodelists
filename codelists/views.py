from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from . import tree_utils
from .coding_systems import CODING_SYSTEMS
from .definition import Definition, build_html_definition
from .models import Codelist


def index(request):
    q = request.GET.get("q")
    if q:
        codelists = Codelist.objects.filter(
            Q(name__contains=q) | Q(description__contains=q)
        )
    else:
        codelists = Codelist.objects.all()
    codelists = codelists.order_by("name")
    ctx = {"codelists": codelists, "q": q}
    return render(request, "codelists/index.html", ctx)


def codelist(request, project_slug, codelist_slug):
    codelist = get_object_or_404(Codelist, project=project_slug, slug=codelist_slug)
    headers, *rows = codelist.table

    if codelist.coding_system_id in ["ctv3", "ctv3tpp"]:
        coding_system = CODING_SYSTEMS["ctv3"]
        subtree = tree_utils.build_subtree(coding_system, codelist.codes)
        definition = Definition.from_codes(codelist.codes, subtree)
        html_definition = build_html_definition(coding_system, subtree, definition)
        html_tree = tree_utils.build_html_tree_highlighting_codes(
            coding_system, subtree, definition
        )
    else:
        html_definition = None
        html_tree = None

    ctx = {
        "codelist": codelist,
        "headers": headers,
        "rows": rows,
        "html_tree": html_tree,
        "html_definition": html_definition,
    }
    return render(request, "codelists/codelist.html", ctx)


def codelist_download(request, project_slug, codelist_slug, version_str):
    codelist = get_object_or_404(Codelist, project=project_slug, slug=codelist_slug)
    if codelist.version_str != version_str:
        raise Http404(
            f"Incorrect version: {version_str}, expected {codelist.version_str}"
        )

    response = HttpResponse(content_type="text/csv")
    content_disposition = 'attachment; filename="{}.csv"'.format(
        codelist.download_filename()
    )
    response["Content-Disposition"] = content_disposition
    response.write(codelist.csv_data)
    return response
