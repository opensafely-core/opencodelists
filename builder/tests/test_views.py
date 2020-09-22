import pytest

from builder import actions
from codelists.search import do_search
from opencodelists.tests.factories import UserFactory

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore::django.utils.deprecation.RemovedInDjango40Warning:debug_toolbar",
    ),
]


def test_codelist(client, tennis_elbow_codelist):
    owner = UserFactory()
    cl = actions.create_codelist(
        owner=owner, name="Elbows", coding_system_id="snomedct"
    )
    search_results = do_search(cl.coding_system, "elbow")
    actions.create_search(codelist=cl, term="elbow", codes=search_results["all_codes"])

    client.force_login(owner)

    rsp = client.get(f"/builder/{owner.username}/{cl.slug}/")

    assert rsp.status_code == 200
    assert b"Elbows" in rsp.content
