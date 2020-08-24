from pathlib import Path

from django.conf import settings
from django.core.management import call_command

from codelists import actions
from codelists.definition import Definition
from codelists.tree_utils import build_subtree
from opencodelists.tests.factories import ProjectFactory

fixtures_path = Path(settings.BASE_DIR, "coding_systems", "snomedct", "fixtures")
call_command("loaddata", fixtures_path / "core-model-components.json")
call_command("loaddata", fixtures_path / "tennis-elbow.json")

with open(fixtures_path / "disorder-of-elbow-excl-arthritis.csv") as f:
    csv_data = f.read()

codelist = actions.create_codelist(
    project=ProjectFactory(),
    name="Test Codelist 2",
    coding_system_id="snomedct",
    description="This is a test",
    methodology="This is how we did it",
    csv_data=csv_data,
)
version = codelist.versions.get()
subtree = build_subtree(codelist.coding_system, version.codes)
Definition.from_codes(version.codes, subtree, 0.5)
