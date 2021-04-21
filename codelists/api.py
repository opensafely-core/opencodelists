from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .actions import (
    create_codelist_with_codes,
    create_version_from_ecl_expr,
    create_version_with_codes,
)
from .api_decorators import require_authentication, require_permission
from .views.decorators import load_codelist, load_owner


@require_http_methods(["GET", "POST"])
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

    request.POST should contain:

        * name
        * coding_system_id
        * codes
        * slug (optional)
    """

    param_keys = ["name", "coding_system_id", "codes"]
    missing_keys = [k for k in param_keys if k not in request.POST]
    if missing_keys:
        return error(f"Missing keys: {', '.join(f'`{k}`' for k in missing_keys)}")

    cl = create_codelist_with_codes(
        owner=owner,
        name=request.POST["name"],
        coding_system_id=request.POST["coding_system_id"],
        codes=request.POST.getlist("codes"),
        slug=request.POST.get("slug"),
    )

    return JsonResponse({"codelist": cl.get_absolute_url()})


@require_http_methods(["POST"])
@require_authentication
@load_codelist
@require_permission
def versions(request, codelist):
    if ("codes" in request.POST and "ecl" in request.POST) or (
        "codes" not in request.POST and "ecl" not in request.POST
    ):
        return error("Provide exactly one of `codes` or `ecl`")

    try:
        if "codes" in request.POST:
            clv = create_version_with_codes(
                codelist=codelist,
                codes=set(request.POST.getlist("codes")),
                tag=request.POST.get("tag"),
            )

        elif "ecl" in request.POST:
            clv = create_version_from_ecl_expr(
                codelist=codelist,
                expr=request.POST["ecl"],
                tag=request.POST.get("tag"),
            )

        else:
            assert False

    except ValueError as e:
        return error(str(e))

    return JsonResponse({"codelist_version": clv.get_absolute_url()})


def error(msg):
    return JsonResponse({"error": msg}, status=400)
