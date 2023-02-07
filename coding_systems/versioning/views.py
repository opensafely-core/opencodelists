from django.shortcuts import render

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
    return render(request, "versioning/latest_releases.html", ctx)
