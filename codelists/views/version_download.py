from django.http import Http404, HttpResponse

from .decorators import load_version


@load_version
def version_download(request, clv, expect_draft):
    if expect_draft != clv.is_draft:
        raise Http404

    response = HttpResponse(content_type="text/csv")
    content_disposition = 'attachment; filename="{}.csv"'.format(
        clv.download_filename()
    )
    response["Content-Disposition"] = content_disposition
    response.write(clv.csv_data)
    return response
