from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from coding_systems.ctv3 import tree_utils as ctv3_tree_utils

from .models import Codelist


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
        if codelist_slug == "ethnicity":
            ix = 1
        else:
            ix = 0

        codes = tuple(sorted({row[ix] for row in rows}))
        tree = ctv3_tree_utils.html_tree_highlighting_codes(codes)
    else:
        tree = None

    ctx = {
        "codelist": codelist,
        "headers": headers,
        "rows": rows,
        "tree": tree,
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
