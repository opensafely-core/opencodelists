from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from opencodelists.models import Organisation

from .actions import create_version_from_ecl_expr, create_version_with_codes
from .views.decorators import load_codelist


@api_view(["GET"])
@permission_classes([])
def codelists(request, organisation_slug):
    """Endpoint to return information about the codelists owned by an organisation.

    HTPP response contains JSON array with one item for each codelist owned by the
    organisation.

    Eg:

    [
        {
            "full_slug": "opensafely/asthma-diagnosis",
            "slug": "asthma-diagnosis",
            "name": "Asthma Diagnosis",
            "versions": [
                {
                    "hash": "66f08cca",
                    "tag": "2020-04-15",
                    "full_slug": "opensafely/asthma-diagnosis/2020-04-15"
                }
            ]
        },
        ...
    ]
    """

    organisation = get_object_or_404(
        Organisation.objects.prefetch_related("codelists__versions"),
        slug=organisation_slug,
    )

    records = []

    for cl in organisation.codelists.all():
        record = {
            "full_slug": cl.full_slug(),
            "slug": cl.slug,
            "name": cl.name,
            "versions": [],
        }
        for version in sorted(cl.versions.all(), key=lambda v: v.created_at):
            record["versions"].append(
                {
                    "hash": version.hash,
                    "tag": version.tag,
                    "full_slug": version.full_slug(),
                }
            )

        records.append(record)
    return Response(records)


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

    if ("codes" in request.data and "ecl" in request.data) or (
        "codes" not in request.data and "ecl" not in request.data
    ):
        return error("Provide exactly one of `codes` or `ecl`")

    try:
        if "codes" in request.data:
            clv = create_version_with_codes(
                codelist=codelist,
                codes=set(request.data.getlist("codes")),
                tag=request.data.get("tag"),
            )

        elif "ecl" in request.data:
            clv = create_version_from_ecl_expr(
                codelist=codelist,
                expr=request.data["ecl"],
                tag=request.data.get("tag"),
            )

        else:
            assert False

    except ValueError as e:
        return error(str(e))

    return Response({"codelist_version": clv.get_absolute_url()})


def error(msg):
    return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)
