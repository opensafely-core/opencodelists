from django.http import HttpResponse

from .decorators import load_version


@load_version
def version_dmd_download(request, clv):
    response = HttpResponse(content_type="text/csv")
    content_disposition = 'attachment; filename="{}-dmd.csv"'.format(
        clv.download_filename()
    )
    response["Content-Disposition"] = content_disposition
    response.write(clv.dmd_csv_data_for_download())
    return response
