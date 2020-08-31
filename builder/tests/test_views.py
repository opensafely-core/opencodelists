from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command

from builder import actions
from codelists.search import do_search
from opencodelists.tests.factories import UserFactory

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore::django.utils.deprecation.RemovedInDjango40Warning:debug_toolbar",
    ),
]


def test_codelist(client):
    fixtures_path = Path(settings.BASE_DIR, "coding_systems", "snomedct", "fixtures")
    call_command("loaddata", fixtures_path / "core-model-components.json")
    call_command("loaddata", fixtures_path / "tennis-elbow.json")

    owner = UserFactory()
    cl = actions.create_codelist(
        owner=owner, name="Elbows", coding_system_id="snomedct"
    )
    search_results = do_search(cl.coding_system, "elbow")
    actions.create_search(
        codelist=cl, term="elbow", codes=search_results["all_codes"],
    )

    client.force_login(owner)

    rsp = client.get(f"/builder/{owner.username}/{cl.slug}/")

    assert rsp.status_code == 200
    assert b"Elbows" in rsp.content
