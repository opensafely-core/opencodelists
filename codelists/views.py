from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect

from . import tree_utils
from .coding_systems import CODING_SYSTEMS
from .definition import Definition, build_html_definition
from .models import Codelist, CodelistVersion


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
    codelist = get_object_or_404(
        Codelist.objects.prefetch_related("versions"),
        project=project_slug,
        slug=codelist_slug,
    )

    version = codelist.versions.order_by("version_str").last()
    return redirect(version)


def version(request, project_slug, codelist_slug, version_str):
    clv = get_object_or_404(
        CodelistVersion.objects.select_related("codelist"),
        codelist__project_id=project_slug,
        codelist__slug=codelist_slug,
        version_str=version_str,
    )
    headers, *rows = clv.table

    if clv.coding_system_id in ["ctv3", "ctv3tpp", "snomedct"]:
        if clv.coding_system_id in ["ctv3", "ctv3tpp"]:
            coding_system = CODING_SYSTEMS["ctv3"]
        else:
            coding_system = CODING_SYSTEMS["snomedct"]
        subtree = tree_utils.build_subtree(coding_system, clv.codes)
        definition = Definition.from_codes(clv.codes, subtree)
        html_definition = build_html_definition(coding_system, subtree, definition)
        if clv.coding_system_id in ["ctv3", "ctv3tpp"]:
            html_tree = tree_utils.build_html_tree_highlighting_codes(
                coding_system, subtree, definition
            )
        else:
            html_tree = None
    else:
        html_definition = None
        html_tree = None

    ctx = {
        "clv": clv,
        "codelist": clv.codelist,
        "headers": headers,
        "rows": rows,
        "html_tree": html_tree,
        "html_definition": html_definition,
    }
    return render(request, "codelists/version.html", ctx)


def download(request, project_slug, codelist_slug, version_str):
    clv = get_object_or_404(
        CodelistVersion.objects.select_related("codelist"),
        codelist__project_id=project_slug,
        codelist__slug=codelist_slug,
        version_str=version_str,
    )
    response = HttpResponse(content_type="text/csv")
    content_disposition = 'attachment; filename="{}.csv"'.format(
        clv.download_filename()
    )
    response["Content-Disposition"] = content_disposition
    response.write(clv.csv_data)
    return response
