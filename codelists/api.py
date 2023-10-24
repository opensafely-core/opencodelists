import json
import re

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from mappings.dmdvmpprevmap.mappers import vmp_ids_to_previous
from opencodelists.models import Organisation, User

from .actions import (
    create_old_style_codelist,
    create_old_style_version,
    create_or_update_codelist,
    create_version_from_ecl_expr,
    create_version_with_codes,
)
from .api_decorators import require_authentication, require_permission
from .models import Codelist, CodelistVersion, Handle
from .views.decorators import load_codelist, load_owner


CODELIST_VERSION_REGEX = re.compile(
    r"""
    # regex for matching codelists from study repos
    (?P<user>user)?/?  # may start with "user/" if it's a user codelist
    (?P<owner>[\w|\d|-]+)/ # organisation slug or user name
    (?P<codelist_slug>[\w|\d|-]+)/ # codelist slug
    (?P<tag_or_hash>[\w|\d|-]+) # version tag or hash
    /?$ # possible trailing slash
    """,
    flags=re.X,
)


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
        * include-users

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
                    "status": "published",
                    "downloadable": True,
                    "updated_date": "2020-04-15"
                }
            ]
        },
        ...
    ]

    Note "downloadable" for a codelist version means that the version is either under review or
    published, and it contains an identifiable code column in the csv data available for
    download. This is important for use with OpenSAFELY Interactive.

    May 2022: The only known production usage of this endpoint is OpenSAFELY Interactive.
    """

    filter_kwargs = {}

    # Only filter on parameters that are present and not the empty string.
    if coding_system_id := request.GET.get("coding_system_id"):
        filter_kwargs["coding_system_id"] = coding_system_id

    if tag := request.GET.get("tag"):
        filter_kwargs["tags__name"] = tag

    records = []

    include_user_codelists = "include-users" in request.GET

    if owner is None:
        codelists = Codelist.objects.all()
    else:
        codelists = owner.codelists

    for cl in sorted(
        codelists.filter(**filter_kwargs).prefetch_related("handles", "versions"),
        key=lambda cl: cl.slug,
    ):
        # Only include organisaion codelists by default
        if not include_user_codelists and not cl.organisation:
            continue

        # If an owner is specified, only return codelists for which the owner is the
        # codelist's current owner
        if owner is not None and cl.owner != owner:
            continue

        record = {
            "full_slug": cl.full_slug(),
            "slug": cl.slug,
            "name": cl.name,
            "coding_system_id": cl.coding_system_id,
            "organisation": cl.organisation.name if cl.organisation else "",
            "user": cl.user.username if cl.user else "",
            "versions": [],
        }
        for version in sorted(cl.versions.all(), key=lambda v: v.created_at):
            record["versions"].append(
                {
                    "hash": version.hash,
                    "tag": version.tag,
                    "full_slug": version.full_slug(),
                    "status": version.status,
                    "downloadable": version.downloadable,
                    "updated_date": version.updated_at.date(),
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
        * codes OR csv_data
        * coding_system_database_alias
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

    code_keys = ["codes", "csv_data"]
    required_keys = [
        "name",
        "coding_system_id",
        "coding_system_database_alias",
    ]
    optional_keys = [
        "slug",
        "tag",
        "description",
        "methodology",
        "references",
        "signoffs",
        "always_create_new_version",
    ]

    if len(set(data) & set(code_keys)) != 1:
        return error("Provide exactly one of `codes` or `csv_data`")

    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        return error(f"Missing keys: {', '.join(f'`{k}`' for k in missing_keys)}")
    extra_keys = [k for k in data if k not in required_keys + optional_keys + code_keys]
    if extra_keys:
        return error(f"Extra keys: {', '.join(f'`{k}`' for k in extra_keys)}")

    if "codes" in data:
        cl = create_or_update_codelist(owner=owner, **data)
    else:
        cl = create_old_style_codelist(owner=owner, **data)

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

    if len(set(data) & {"codes", "csv_data", "ecl"}) != 1:
        return error("Provide exactly one of `codes`, `csv_data` or `ecl`")

    try:
        if "codes" in data:
            clv = create_version_with_codes(
                codelist=codelist,
                codes=set(data["codes"]),
                tag=data.get("tag"),
                coding_system_database_alias=data["coding_system_database_alias"],
                always_create_new_version=data.get("always_create_new_version", False),
            )
        elif "csv_data" in data:
            clv = create_old_style_version(
                codelist=codelist,
                csv_data=data["csv_data"],
                tag=data.get("tag"),
                coding_system_database_alias=data["coding_system_database_alias"],
            )
        elif "ecl" in data:
            clv = create_version_from_ecl_expr(
                codelist=codelist,
                expr=data["ecl"],
                tag=data.get("tag"),
                coding_system_database_alias=data["coding_system_database_alias"],
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


@require_http_methods(["GET"])
def dmd_previous_codes_mapping(request):
    """
    Return a mapping of dm+d VMP ID to previous VMP IDs

    dm+d VPM IDs can change.  When they do, the data we obtain in the coding system release
    contains a record of the previous VMP ID.  Any system using a dm+d codelist with a
    VMP ID needs to also look up any previous or subsequent IDs in order to avoid missing
    medications.

    This endpoint is intended to be used by backends to determine any additional related codes
    to include with set of dm+d codes.
    """
    _, vmp_to_previous_tuples = vmp_ids_to_previous()
    return JsonResponse(vmp_to_previous_tuples, safe=False)


@require_http_methods("POST")
@csrf_exempt
def codelists_check(requests):
    """
    Checks that a study repo's codelist CSV files as downloaded now are consistent
    with the study's current downloaded codelists.
    study_codelists: the contents of a study repo's codelists.txt
    manifest: the contents of a study repo's codelists.json; this file is generated
    when codelists are downloaded into a study using `opensafely codelists update`
    and contain a hash of the codelist CSV file data at the time of update.

    Note that some of these checks are duplicated in opensafely-cli and will fail the
    Github action test run (`opensafely codelists check`). However, we can't guarantee
    that a user has corrected those errors, so we need to check them again.

    We DO NOT check whether the actual downloaded codelists have been modified; this can
    only be done in the study repo itself (either CLI or GA).
    """
    study_codelists = requests.POST.get("codelists")
    try:
        manifest = json.loads(requests.POST.get("manifest"))
    except json.decoder.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "data": {"error": "Codelists manifest file is invalid"}}
        )

    codelist_download_data = {}
    # Fetch codelist CSV data
    for line in study_codelists.split("\n"):
        line = line.strip().rstrip("/")
        if not line or line.startswith("#"):
            continue
        matches = CODELIST_VERSION_REGEX.match(line)
        if not matches:
            return JsonResponse(
                {
                    "status": "error",
                    "data": {
                        "error": f"{line} does not match expected codelist pattern"
                    },
                }
            )

        line_parts = matches.groupdict()
        try:
            codelist_version = CodelistVersion.objects.get_by_hash(
                line_parts["tag_or_hash"]
            )
        except (CodelistVersion.DoesNotExist, ValueError):
            # it's an old version that predates hashes, find by owner/org
            owner = line_parts["owner"]
            codelist_slug = line_parts["codelist_slug"]
            try:
                if line_parts["user"]:
                    user = User.objects.get(username=owner)
                    handle = Handle.objects.get(slug=codelist_slug, user=user)
                else:
                    organisation = Organisation.objects.get(slug=owner)
                    handle = Handle.objects.get(
                        slug=codelist_slug, organisation=organisation
                    )
                codelist_version = CodelistVersion.objects.get(
                    codelist=handle.codelist, tag=line_parts["tag_or_hash"]
                )
            except (
                User.DoesNotExist,
                Handle.DoesNotExist,
                Organisation.DoesNotExist,
                CodelistVersion.DoesNotExist,
            ):
                return JsonResponse(
                    {"status": "error", "data": {"error": f"{line} could not be found"}}
                )
        codelist_download_data[line] = codelist_version.csv_data_sha()

    # Compare with manifest file
    # The manifest file is generated when `opensafely codelists update` is run in a study repo
    # It contains an entry per codelist file with a hash of the file content and represents the
    # state of the last update in the study repo
    # codelist_download_data is the download data corresponding to the files listed in the study
    # repo's codelists.csv
    # We can check whether the codelists in the study repo are up to date by comparing the
    # similarly-hashed content of the data that would be prepared for a CSV download
    manifest_codelist_ids = set(file["id"] for file in manifest["files"].values())
    current_codelist_ids = set(codelist_download_data.keys())
    # new files are files that are in the study's codelists.csv but not in the manifest file generatated
    # at the last update
    new_files = current_codelist_ids - manifest_codelist_ids
    # removed files are codelist entries that have been removed from the study's codelists.csv since
    # the last update
    removed_files = manifest_codelist_ids - current_codelist_ids
    changed = [
        file_data["id"]
        for file_data in manifest["files"].values()
        if file_data["id"] in codelist_download_data
        and file_data["sha"] != codelist_download_data[file_data["id"]]
    ]
    if new_files or removed_files or changed:
        return JsonResponse(
            {
                "status": "error",
                "data": {
                    "added": list(new_files),
                    "removed": list(removed_files),
                    "changed": changed,
                },
            }
        )
    return JsonResponse({"status": "ok"})
