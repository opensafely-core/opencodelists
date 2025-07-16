import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from codelists.coding_systems import CODING_SYSTEMS


def latest_releases(request):
    """List latest releases for each coding system"""

    ctx = {
        "latest_releases": [
            cs.get_by_release_or_most_recent()
            for cs in CODING_SYSTEMS.values()
            if cs.has_database
        ]
    }

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
        return JsonResponse(data)

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
