from django.http import HttpResponse

from .decorators import load_version


@load_version
def version_download_definition(request, clv):
    try:
        response = HttpResponse(content_type="text/csv")
        content_disposition = (
            f'attachment; filename="{clv.download_filename()}-definition.csv"'
        )
        response["Content-Disposition"] = content_disposition
        response.write(clv.definition_csv_data_for_download())
        return response
    except ValueError as e:
        if str(e) == "Codelist version does not have a codeset":
            return HttpResponse(
                "This codelist version does not have a codeset.",
                status=400,
            )
        raise e
