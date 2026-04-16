#!/usr/bin/env python
"""Print SNOMED usage over time for one concept.

Usage:
    python scripts/show_snomed_usage_history.py [SNOMED_CODE]

If no code is provided, a code is selected at random from imported usage data.
"""

import os
import random
import sys
from pathlib import Path

import django


# Ensure project imports resolve even when this script is run from a different cwd.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opencodelists.settings")
django.setup()

from coding_systems.usage.models import CodeUsageEntry  # noqa: E402


def format_usage(value):
    if value is None:
        return "<5"
    return f"{value:,}"


def choose_code():
    codes = list(
        CodeUsageEntry.objects.filter(release__coding_system="snomedct")
        .order_by()
        .values_list("code", flat=True)
        .distinct()
    )
    if not codes:
        raise SystemExit("No SNOMED usage imports found.")
    return random.choice(codes)


def get_code_arg():
    for arg in sys.argv[1:]:
        if arg.isdigit():
            return arg
    return None


def main():
    code = get_code_arg() or choose_code()
    rows = list(
        CodeUsageEntry.objects.filter(release__coding_system="snomedct", code=code)
        .select_related("release")
        .order_by("release__period")
    )

    if not rows:
        raise SystemExit(f"No usage data found for SNOMED code {code}.")

    period_width = max(len("Period"), *(len(row.release.period) for row in rows))
    usage_width = max(len("Usage"), *(len(format_usage(row.usage)) for row in rows))

    print(f"SNOMED code: {code}")
    print()
    print(f"{'Period':<{period_width}}  {'Usage':>{usage_width}}")
    print(f"{'-' * period_width}  {'-' * usage_width}")
    for row in rows:
        print(
            f"{row.release.period:<{period_width}}  {format_usage(row.usage):>{usage_width}}"
        )


if __name__ == "__main__":
    main()
