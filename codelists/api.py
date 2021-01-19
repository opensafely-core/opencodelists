from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .actions import create_version_from_ecl_expr
from .views.decorators import load_codelist


@api_view(["POST"])
@load_codelist
def versions(request, codelist):
    if codelist.organisation:
        assert not codelist.user
        if not request.user.is_member(codelist.organisation):
            raise PermissionDenied
    else:
        assert codelist.user
        if request.user != codelist.user:
            raise PermissionDenied

    if "ecl" not in request.data:
        return error("Missing `ecl` key")

    try:
        clv = create_version_from_ecl_expr(
            codelist=codelist, expr=request.data["ecl"], tag=request.data.get("tag")
        )
    except ValueError as e:
        return error(str(e))

    return Response({"codelist_version": clv.get_absolute_url()})


def error(msg):
    return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)
