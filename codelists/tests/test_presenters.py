from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command

from codelists import presenters
from codelists.definition import Definition
from codelists.hierarchy import Hierarchy

from .factories import create_codelist

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore::django.utils.deprecation.RemovedInDjango40Warning:debug_toolbar",
    ),
]


def test_build_html_tree_highlighting_codes():
    fixtures_path = Path(settings.BASE_DIR, "coding_systems", "snomedct", "fixtures")
    call_command("loaddata", fixtures_path / "core-model-components.json")
    call_command("loaddata", fixtures_path / "tennis-elbow.json")

    with open(fixtures_path / "disorder-of-elbow-excl-arthritis.csv") as f:
        cl = create_codelist(csv_data=f.read())

    coding_system = cl.coding_system
    clv = cl.versions.get()
    hierarchy = Hierarchy.from_codes(coding_system, clv.codes)
    definition = Definition.from_codes(set(clv.codes), hierarchy)

    html = presenters.build_html_tree_highlighting_codes(
        coding_system, hierarchy, definition
    )

    with open(
        Path(settings.BASE_DIR, "codelists", "tests", "expected_html_tree.html")
    ) as f:
        assert html.strip() == f.read().strip()
