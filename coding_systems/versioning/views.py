import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from codelists.coding_systems import CODING_SYSTEMS
from coding_systems.versioning.models import PCDRefsetVersion


def latest_releases(request):
    """List latest releases for each coding system"""

    # Get regular coding system releases
    coding_system_releases = [
        cs.get_by_release_or_most_recent()
        for cs in CODING_SYSTEMS.values()
        if cs.has_database
    ]

    # Get the latest PCD refset version
    latest_pcd = PCDRefsetVersion.get_latest()
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
        return JsonResponse(data)

    if latest_pcd:
        ctx["pcd_refset_version"] = latest_pcd
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
