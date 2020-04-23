import csv
from io import StringIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Codelist


def index(request):
    ctx = {"codelists": Codelist.objects.order_by("name")}
    return render(request, "codelists/index.html", ctx)


def codelist(request, project_slug, codelist_slug):
    codelist = get_object_or_404(Codelist, project=project_slug, slug=codelist_slug)
    table = list(csv.reader(StringIO(codelist.csv_data)))
    headers, *rows = table

    ctx = {
        "codelist": codelist,
        "headers": headers,
        "rows": rows,
    }
    return render(request, "codelists/codelist.html", ctx)


def codelist_download(request, project_slug, codelist_slug):
    codelist = get_object_or_404(Codelist, project=project_slug, slug=codelist_slug)
    response = HttpResponse(content_type="text/csv")
    content_disposition = 'attachment; filename="{}.csv"'.format(
        codelist.download_filename()
    )
    response["Content-Disposition"] = content_disposition
    response.write(codelist.csv_data)
    return response
