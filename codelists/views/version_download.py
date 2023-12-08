from django.http import HttpResponse, HttpResponseBadRequest

from .decorators import load_version


@load_version
def version_download(request, clv):
    fixed_headers = "fixed-headers" in request.GET
    omit_mapped_vmps = "omit-mapped-vmps" in request.GET
    if fixed_headers and not clv.downloadable:
        return HttpResponseBadRequest("Codelist is not downloadable")
    response = HttpResponse(content_type="text/csv")
    content_disposition = f'attachment; filename="{clv.download_filename()}.csv"'
    response["Content-Disposition"] = content_disposition
    response.write(
        clv.csv_data_for_download(
            fixed_headers=fixed_headers, include_mapped_vmps=not omit_mapped_vmps
        )
    )
    return response
