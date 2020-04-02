import csv

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import Codelist


def index(request):
    ctx = {"codelists": Codelist.objects.all()}
    return render(request, "codelists/index.html", ctx)


def codelist(request, publisher_slug, codelist_slug):
    codelist = get_object_or_404(Codelist, publisher=publisher_slug, slug=codelist_slug)

    coding_system = request.GET.get("coding_system")
    version_str = request.GET.get("version")
    format_ = request.GET.get("format")

    if format_:
        # When accessing via API, must specify coding_system and version_str
        assert format_ in ["csv", "json"]
        assert coding_system
        assert version_str

    if coding_system and coding_system != codelist.coding_system:
        assert False

    if version_str:
        version = codelist.versions.get(version_str=version_str)
    else:
        version = codelist.versions.order_by("version_str").last()

    other_versions = codelist.versions.exclude(version_str=version.version_str)

    codes = [m.code for m in version.members.all()]

    if format_ == "csv":
        response = HttpResponse(content_type="text/csv")
        content_disposition = 'attachment; filename="{}.csv"'.format(
            version.download_filename()
        )
        response["Content-Disposition"] = content_disposition
        writer = csv.writer(response)
        writer.writerow([coding_system])
        writer.writerows([c] for c in codes)
        return response

    elif format_ == "json":
        json_data = {
            "url": _build_api_url(request, codelist, "json", domain=True),
            "codelist": codelist.full_slug(),
            "coding_system": coding_system,
            "version": version_str,
            "codes": codes,
        }
        response = JsonResponse(json_data, json_dumps_params={"indent": 2})
        content_disposition = 'attachment; filename="{}.json"'.format(
            version.download_filename()
        )
        response["Content-Disposition"] = content_disposition
        return response

    elif format_:
        assert False

    ctx = {
        "codelist": codelist,
        "version": version,
        "other_versions": other_versions,
        "codes": codes,
        "download_csv_url": _build_api_url(request, codelist, "csv"),
        "download_json_url": _build_api_url(request, codelist, "json"),
    }
    return render(request, "codelists/codelist.html", ctx)


def _build_api_url(request, codelist, format_, domain=False):
    params = request.GET.copy()
    params["format"] = format_
    params["coding_system"] = codelist.coding_system
    path_plus_qs = request.path + "?" + params.urlencode()

    if domain:
        # TODO don't hardcode this
        return "https://opencodelists.net" + path_plus_qs
    else:
        return path_plus_qs
