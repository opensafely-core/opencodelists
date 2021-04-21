import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .actions import (
    create_codelist_with_codes,
    create_version_from_ecl_expr,
    create_version_with_codes,
)
from .api_decorators import require_authentication, require_permission
from .views.decorators import load_codelist, load_owner


@require_http_methods(["GET", "POST"])
@csrf_exempt
@load_owner
def codelists(request, owner):
    if request.method == "GET":
        return codelists_get(request, owner)
    else:
        return codelists_post(request, owner)


def codelists_get(request, owner):
    """Return information about the codelists owned by an organisation.

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

    records = []

    for cl in owner.codelists.prefetch_related("versions").all():
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
    return JsonResponse({"codelists": records})


@require_authentication
@require_permission
def codelists_post(request, owner):
    """Create new codelist for owner.

    request.body should contain:

        * name
        * coding_system_id
        * codes
        * slug (optional)
        * tag (optional)
        * description (optional)
        * methodology (optional)
        * references (optional)
        * signoffs (optional)
    """

    try:
        data = json.loads(request.body)
    except json.decoder.JSONDecodeError:
        return error("Invalid JSON")

    required_keys = ["name", "coding_system_id", "codes"]
    optional_keys = [
        "slug",
        "tag",
        "description",
        "methodology",
        "references",
        "signoffs",
    ]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        return error(f"Missing keys: {', '.join(f'`{k}`' for k in missing_keys)}")
    extra_keys = [k for k in data if k not in required_keys + optional_keys]
    if extra_keys:
        return error(f"Extra keys: {', '.join(f'`{k}`' for k in extra_keys)}")

    cl = create_codelist_with_codes(owner=owner, **data)

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
            )

        elif "ecl" in data:
            clv = create_version_from_ecl_expr(
                codelist=codelist,
                expr=data["ecl"],
                tag=data.get("tag"),
            )

        else:
            assert False

    except ValueError as e:
        return error(str(e))

    return JsonResponse({"codelist_version": clv.get_absolute_url()})


def error(msg):
    return JsonResponse({"error": msg}, status=400)
