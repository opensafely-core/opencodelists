from builder import actions
from codelists.search import do_search
from opencodelists.tests.factories import UserFactory


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


def test_search(client, tennis_elbow_codelist):
    owner = UserFactory()
    cl = actions.create_codelist(
        owner=owner, name="Elbows", coding_system_id="snomedct"
    )
    search_results = do_search(cl.coding_system, "elbow")
    actions.create_search(codelist=cl, term="elbow", codes=search_results["all_codes"])

    client.force_login(owner)

    rsp = client.get(f"/builder/{owner.username}/{cl.slug}/search/elbow/")

    assert rsp.status_code == 200
    assert b'Search term: "elbow"' in rsp.content


def test_no_search_term(client, tennis_elbow_codelist):
    owner = UserFactory()
    cl = actions.create_codelist(
        owner=owner, name="Elbows", coding_system_id="snomedct"
    )
    search_results = do_search(cl.coding_system, "elbow")
    actions.create_search(codelist=cl, term="elbow", codes=search_results["all_codes"])

    client.force_login(owner)

    rsp = client.get(f"/builder/{owner.username}/{cl.slug}/no-search-term/")

    assert rsp.status_code == 200
    assert b"No search term" in rsp.content
