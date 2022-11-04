import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .actions import (
    create_or_update_codelist,
    create_version_from_ecl_expr,
    create_version_with_codes,
)
from .api_decorators import require_authentication, require_permission
from .models import Codelist
from .views.decorators import load_codelist, load_owner


@require_http_methods(["GET"])
def all_codelists(request):
    return codelists_get(request)


@require_http_methods(["GET", "POST"])
@csrf_exempt
@load_owner
def codelists(request, owner):
    if request.method == "GET":
        return codelists_get(request, owner)
    else:
        return codelists_post(request, owner)


def codelists_get(request, owner=None):
    """Return information about the codelists owned by an organisation.

    HTPP response contains JSON array with one item for each codelist owned by the
    organisation.

    request.GET may contain the following parameters to filter the returned codelists:

        * coding_system_id
        * tag

    Eg:

    [
        {
            "full_slug": "opensafely/asthma-diagnosis",
            "slug": "asthma-diagnosis",
            "name": "Asthma Diagnosis",
            "coding_system_id": "snomedct",
            "organisation: "OpenSAFELY,
            "versions": [
                {
                    "hash": "66f08cca",
                    "tag": "2020-04-15",
                    "full_slug": "opensafely/asthma-diagnosis/2020-04-15",
                    "status": "published"
                }
            ]
        },
        ...
    ]

    May 2022: The only known production usage of this endpoint is OpenSAFELY Interactive.
    """

    filter_kwargs = {}

    # Only filter on parameters that are present and not the empty string.
    if coding_system_id := request.GET.get("coding_system_id"):
        filter_kwargs["coding_system_id"] = coding_system_id

    if tag := request.GET.get("tag"):
        filter_kwargs["tags__name"] = tag

    records = []

    if owner is None:
        codelists = Codelist.objects.all()
    else:
        codelists = owner.codelists

    for cl in sorted(
        codelists.filter(**filter_kwargs).prefetch_related("handles", "versions"),
        key=lambda cl: cl.slug,
    ):
        record = {
            "full_slug": cl.full_slug(),
            "slug": cl.slug,
            "name": cl.name,
            "coding_system_id": cl.coding_system_id,
            "organisation": cl.organisation.name if cl.organisation else "",
            "versions": [],
        }
        for version in sorted(cl.versions.all(), key=lambda v: v.created_at):
            record["versions"].append(
                {
                    "hash": version.hash,
                    "tag": version.tag,
                    "full_slug": version.full_slug(),
                    "status": version.status,
                }
            )

        records.append(record)
    return JsonResponse({"codelists": records})


@require_authentication
@require_permission
def codelists_post(request, owner):
    """Create new codelist for owner.

    request.body should contain:

        * name
        * coding_system_id
        * codes
        * coding_system_database_alias (optional)
        * slug (optional)
        * tag (optional)
        * description (optional)
        * methodology (optional)
        * references (optional)
        * signoffs (optional)
        * always_create_new_version (optional)
    """

    try:
        data = json.loads(request.body)
    except json.decoder.JSONDecodeError:
        return error("Invalid JSON")

    required_keys = ["name", "coding_system_id", "codes"]
    optional_keys = [
        "coding_system_database_alias",
        "slug",
        "tag",
        "description",
        "methodology",
        "references",
        "signoffs",
        "always_create_new_version",
    ]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        return error(f"Missing keys: {', '.join(f'`{k}`' for k in missing_keys)}")
    extra_keys = [k for k in data if k not in required_keys + optional_keys]
    if extra_keys:
        return error(f"Extra keys: {', '.join(f'`{k}`' for k in extra_keys)}")

    cl = create_or_update_codelist(owner=owner, **data)

    return JsonResponse({"codelist": cl.get_absolute_url()})


@require_http_methods(["POST"])
@csrf_exempt
@require_authentication
@load_codelist
@require_permission
def versions(request, codelist):
    try:
        data = json.loads(request.body)
    except json.decoder.JSONDecodeError:
        return error("Invalid JSON")

    if ("codes" in data and "ecl" in data) or (
        "codes" not in data and "ecl" not in data
    ):
        return error("Provide exactly one of `codes` or `ecl`")

    try:
        if "codes" in data:
            clv = create_version_with_codes(
                codelist=codelist,
                codes=set(data["codes"]),
                tag=data.get("tag"),
                coding_system_database_alias=data.get("coding_system_database_alias"),
                always_create_new_version=data.get("always_create_new_version", False),
            )

        elif "ecl" in data:
            clv = create_version_from_ecl_expr(
                codelist=codelist,
                expr=data["ecl"],
                tag=data.get("tag"),
                coding_system_database_alias=data.get("coding_system_database_alias"),
            )

        else:
            assert False

    except ValueError as e:
        return error(str(e))

    if clv is None:
        return error("No difference to previous version")

    return JsonResponse({"codelist_version": clv.get_absolute_url()})


def error(msg):
    return JsonResponse({"error": msg}, status=400)
