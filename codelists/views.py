from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Codelist


def index(request):
    ctx = {"codelists": Codelist.objects.all()}
    return render(request, "codelists/index.html", ctx)


def codelist(request, project_slug, codelist_slug):
    codelist = get_object_or_404(Codelist, project=project_slug, slug=codelist_slug)
    ctx = {"codelist": codelist}
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
