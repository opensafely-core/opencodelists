"""RESTful API for interacting with codelists and related resources.

Endpoints are used by some OpenSAFELY components and other clients. Method
docstrings may list known clients, though this list is not exhaustive and
reflects a specific point in time. This does not imply tight coupling or that
the OpenCodelists owner is responsible for those clients. However, notifying
client owners about new endpoints, parameters, or API versions can be helpful
where relevant. Identifying clients may also aid user research.

Non-backward-compatible changes to API contracts should be scoped to a new
/api/vN/ base path. Examples include modifying outputs, methods, or accepted
parameters of existing endpoints. This approach ensures existing clients remain
functional. New endpoints, methods, and parameters can be added without
requiring a new version.
"""

import json
import re

from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from opencodelists.models import Organisation, User

from .actions import (
    create_old_style_codelist,
    create_old_style_version,
    create_or_update_codelist,
    create_version_from_ecl_expr,
    create_version_with_codes,
    update_codelist,
)
from .api_decorators import require_authentication, require_permission
from .models import Codelist, CodelistVersion, Handle, Status
from .views.decorators import load_codelist, load_owner


CODELIST_VERSION_REGEX = re.compile(
    r"""
    # regex for matching codelists from study repos
    (?P<user>user)?/?  # may start with "user/" if it's a user codelist
    (?P<owner>[\w|\d|-]+)/ # organisation slug or user name
    (?P<codelist_slug>[\w|\d|-]+)/ # codelist slug
    # version tag or hash; a tag can technically be any character,
    # but exclude forward slashes, since they'd break the urls anyway.
    (?P<tag_or_hash>[^\/]+)
    /?$ # possible trailing slash
    """,
    flags=re.X,
)


@require_http_methods(["GET"])
def all_codelists(request):
    """Return information about all codelists.

    Parameters and response as in codelists_get.

    Known clients (see caveats in module docstring):
        2024-Nov: no known production clients.
    """
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

    Known clients (see caveats in module docstring):
        2024-Nov: Used by opensafely-cli when updating codelists and when
            validating its OpenCodelists API wrapper.
        2024-Nov: Used in OpenSAFELY Interactive to get all SNOMEDCT and DMD
            codelists for reference when creating an analysis request.
        2024-Nov: Used by the code usage explorer
            https://github.com/ebmdatalab/codeusage/ which is stood up at
            https://milanwiedemann.shinyapps.io/codeusage/ This uses the API to
            allow filtering usage stats by an OpenCodelists codelist.
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
        codelists.filter(**filter_kwargs)
        .annotate(handle_count=Count("handles"))
        .filter(handle_count=1)
        .prefetch_related("handles", "versions"),
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

        if "description" in request.GET:
            record["description"] = cl.description

        if "methodology" in request.GET:
            record["methodology"] = cl.methodology

        if "references" in request.GET:
            record["references"] = []
            for reference in cl.references.all():
                record["references"].append(
                    {
                        "text": reference.text,
                        "url": reference.url,
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
        # ignore_unfound_codes (optional)

    Known clients (see caveats in module docstring):
        2024-Nov: Scripts such as those in /codelists/scripts/ may use this
            endpoint to do batch upload of codelists.
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
        "ignore_unfound_codes",
        "new_slug",
        "should_publish",
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
    """Create new version of existing codelist.

    request.body should contain one of:
        * codes
        * csv_data
        * ecl

    ... and:
        * tag
        * coding_system_database_alias
        * always_create_new_version (optional, for "codes" / new-style only.)
        * ignore_unfound_codes (optional, for "codes" / new-style only.)
        * name (optional, if passed overwrite the current name)
        * description (optional, if passed overwrite the current description)
        * should_publish (optional, if passed forces the new version to be published)


    Known clients (see caveats in module docstring):
        2024-Nov: Scripts such as those in /codelists/scripts/ may use this
            endpoint to do batch upload of codelists.
    """
    try:
        data = json.loads(request.body)
    except json.decoder.JSONDecodeError:
        return error("Invalid JSON")

    if len(set(data) & {"codes", "csv_data", "ecl"}) != 1:
        return error("Provide exactly one of `codes`, `csv_data` or `ecl`")

    if "description" in data or "name" in data or "new_slug" in data:
        update_codelist(
            owner=codelist.owner,
            name=data.get("name", codelist.name),
            slug=data.get("new_slug", codelist.slug),
            codelist=codelist,
            description=data.get("description", codelist.description),
            methodology=codelist.methodology,
            references=[
                {"url": reference.url, "text": reference.text}
                for reference in codelist.references.all()
            ],
            signoffs=[
                {"user": signoff.user, "date": signoff.date}
                for signoff in codelist.signoffs.all()
            ],
        )

    try:
        if "codes" in data:
            clv = create_version_with_codes(
                codelist=codelist,
                codes=set(data["codes"]),
                status=Status.PUBLISHED
                if data.get("should_publish", False)
                else Status.UNDER_REVIEW,
                tag=data.get("tag"),
                coding_system_database_alias=data["coding_system_database_alias"],
                always_create_new_version=data.get("always_create_new_version", False),
                ignore_unfound_codes=data.get("ignore_unfound_codes", False),
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


    Known clients (see caveats in module docstring):
        2024-Nov: Used in opensafely-cli when checking codelists are current in
            actions.
        2024-Nov: Used in Job Server when creating a job request and when
            validating its OpenCodelists API wrapper.
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
        if not codelist_version.downloadable:
            return JsonResponse(
                {"status": "error", "data": {"error": f"{line} is not downloadable"}}
            )
        codelist_download_data[line] = codelist_version.csv_data_shas()

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
    # new files are files that are in the study's codelists.csv but not in the manifest file generated
    # at the last update
    new_files = current_codelist_ids - manifest_codelist_ids
    # removed files are codelist entries that have been removed from the study's codelists.csv since
    # the last update
    removed_files = manifest_codelist_ids - current_codelist_ids
    changed = [
        file_data["id"]
        for file_data in manifest["files"].values()
        if file_data["id"] in codelist_download_data
        and file_data["sha"] not in codelist_download_data[file_data["id"]]
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
