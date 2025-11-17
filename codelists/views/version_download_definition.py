from django.http import HttpResponse

from codelists.presenters import present_definition_for_download
from opencodelists.csv_utils import rows_to_csv_data

from .decorators import load_version


@load_version
def version_download_definition(request, clv):
    try:
        response = HttpResponse(content_type="text/csv")
        content_disposition = (
            f'attachment; filename="{clv.download_filename()}-definition.csv"'
        )
        response["Content-Disposition"] = content_disposition
        response.write(rows_to_csv_data(present_definition_for_download(clv)))
        return response
    except ValueError as e:
        if str(e) == "Codelist version does not have a codeset":
            return HttpResponse(
                "This codelist version does not have a codeset.",
                status=400,
            )
        raise e
