from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from .coding_systems import CODING_SYSTEMS
from .definition import html_definition
from .models import Codelist
from .tree_utils import html_tree_highlighting_codes


def index(request):
    q = request.GET.get("q")
    if q:
        codelists = Codelist.objects.filter(name__contains=q, description__contains=q)
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
        if codelist_slug == "ethnicity":
            ix = 1
        else:
            ix = 0

        codes = tuple(sorted({row[ix] for row in rows}))
        tree = html_tree_highlighting_codes(coding_system, codes)
        definition = html_definition(coding_system, codes)
    else:
        tree = None
        definition = None

    ctx = {
        "codelist": codelist,
        "headers": headers,
        "rows": rows,
        "tree": tree,
        "definition": definition,
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
