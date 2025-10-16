import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from codelists.api_decorators import require_authentication
from codelists.coding_systems import CODING_SYSTEMS
from coding_systems.versioning.models import NHSDrugRefsetVersion, PCDRefsetVersion
from opencodelists.models import Organisation


def latest_releases(request):
    """List latest releases for each coding system"""

    # Get regular coding system releases
    coding_system_releases = [
        cs.get_by_release_or_most_recent()
        for cs in CODING_SYSTEMS.values()
        if cs.has_database
    ]

    # Get the latest PCD refset version and the latest NHS drug refset version
    latest_pcd = PCDRefsetVersion.get_latest()
    latest_drug = NHSDrugRefsetVersion.get_latest()
    ctx = {"latest_releases": coding_system_releases}

    if request.GET.get("type") == "json":
        data = {
            lr.id: {
                "name": lr.name,
                "release_name": lr.release_name,
                "valid_from": lr.release.valid_from,
                "import_timestamp": lr.release.import_timestamp,
                "database_alias": lr.database_alias,
            }
            for lr in ctx["latest_releases"]
        }
        # Add PCD refset data if available
        if latest_pcd:
            data["pcd_refsets"] = {
                "release": latest_pcd.release,
                "tag": latest_pcd.tag,
                "valid_from": latest_pcd.release_date.isoformat(),
                "import_timestamp": latest_pcd.import_timestamp.isoformat(),
            }
        # Add NHS drug refset data if available
        if latest_drug:
            data["nhs_drug_refsets"] = {
                "release": latest_drug.release,
                "tag": latest_drug.tag,
                "valid_from": latest_drug.release_date.isoformat(),
                "import_timestamp": latest_drug.import_timestamp.isoformat(),
            }
        return JsonResponse(data)

    if latest_pcd:
        ctx["pcd_refset_version"] = latest_pcd
    if latest_drug:
        ctx["nhs_drug_refset_version"] = latest_drug
    return render(request, "versioning/latest_releases.html", ctx)


@require_http_methods(["POST"])
def more_info(request, coding_system):
    if coding_system not in CODING_SYSTEMS:
        return JsonResponse({"error": "Invalid coding system"})

    try:
        data = json.loads(request.body)
        codes = data.get("codes", [])
    except Exception:
        return JsonResponse({"error": "Badly formatted JSON request"})

    cs = CODING_SYSTEMS[coding_system].get_by_release_or_most_recent()
    synonyms = {"synonyms": cs.lookup_synonyms(codes)}
    references = {"references": cs.lookup_references(codes)}
    return JsonResponse(synonyms | references)


@csrf_exempt
@require_authentication
@require_http_methods(["POST"])
def update_refset_version(request, refset_type):
    """
    API endpoint to update NHS refset versions (PCD or Drug).
    Only users who are members of the corresponding organisation can update.
    """
    # Map refset type to organisation and model
    REFSET_CONFIG = {
        "pcd": {
            "organisation_slug": "nhsd-primary-care-domain-refsets",
            "model": PCDRefsetVersion,
        },
        "drug": {
            "organisation_slug": "nhs-drug-refsets",
            "model": NHSDrugRefsetVersion,
        },
    }

    if refset_type not in REFSET_CONFIG:
        return JsonResponse(
            {"error": "Invalid refset type. Must be 'pcd' or 'drug'"}, status=400
        )

    config = REFSET_CONFIG[refset_type]

    # Check user has permission (member of the organisation)
    organisation = Organisation.objects.get(slug=config["organisation_slug"])

    if not request.user.is_member(organisation):
        return JsonResponse(
            {
                "error": f"Unauthorised. You must be a member of {organisation.name} to update this refset version."
            },
            status=403,
        )

    # Parse request body
    try:
        from datetime import datetime

        data = json.loads(request.body)
        release = data.get("release")
        tag = data.get("tag")
        release_date_str = data.get("release_date")

        if not all([release, tag, release_date_str]):
            return JsonResponse(
                {"error": "Missing required fields: release, tag, release_date"},
                status=400,
            )

        # Parse the release_date string to a date object
        try:
            release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse(
                {"error": "Invalid release_date format. Expected YYYY-MM-DD"},
                status=400,
            )
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({"error": f"Invalid JSON: {str(e)}"}, status=400)

    # Create the new refset version
    try:
        refset_version = config["model"].objects.create(
            release=release,
            tag=tag,
            release_date=release_date,
        )
        return JsonResponse(
            {
                "success": True,
                "message": f"Created new {config['model'].__name__} version: {tag}",
                "version": {
                    "release": refset_version.release,
                    "tag": refset_version.tag,
                    "release_date": refset_version.release_date.isoformat(),
                    "import_timestamp": refset_version.import_timestamp.isoformat(),
                },
            },
            status=201,
        )
    except Exception as e:
        return JsonResponse(
            {"error": f"Failed to create version: {str(e)}"}, status=500
        )
