#!/usr/bin/env python
"""Remove the N most recently imported SNOMED usage periods from the database.

Useful for testing partial imports without having to wipe everything.

Usage:
    just manage shell < scripts/remove_snomed_usage_imports.py  # removes 1
    N=3 just manage shell < scripts/remove_snomed_usage_imports.py

Or run directly (after sourcing .env):
    python scripts/remove_snomed_usage_imports.py [N]

where N defaults to 1.
"""

import os
import sys
from pathlib import Path

import django


# Ensure project imports resolve even when this script is run from a different cwd.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opencodelists.settings")
django.setup()

from coding_systems.usage.models import CodeUsageRelease  # noqa: E402


def get_count_arg(default=1):
    """Return the delete count from argv/env, compatible with manage.py shell."""
    # Prefer first integer argv item, so this works with:
    # - python scripts/remove_snomed_usage_imports.py 3
    # - python manage.py shell < scripts/remove_snomed_usage_imports.py
    for arg in sys.argv[1:]:
        try:
            return int(arg)
        except ValueError:
            continue
    return int(os.environ.get("N", default))


n = get_count_arg(default=1)
if n < 0:
    raise ValueError("N must be >= 0")

releases = list(
    CodeUsageRelease.objects.filter(coding_system="snomedct").order_by("-imported_at")[
        :n
    ]
)

if not releases:
    print("No imports found.")
    sys.exit(0)

for release in releases:
    # Count entries for this release
    from coding_systems.usage.models import CodeUsageEntry

    entry_count = CodeUsageEntry.objects.filter(release=release).count()
    release.delete()
    print(f"Deleted period {release.period} ({entry_count} entries).")
