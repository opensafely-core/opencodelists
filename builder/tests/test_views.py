from builder import actions
from codelists import actions as codelist_actions
from codelists.search import do_search
from opencodelists.tests.factories import UserFactory


def test_draft(client, tennis_elbow_codelist):
    cl = tennis_elbow_codelist
    converted_clv = codelist_actions.convert_codelist_to_new_style(codelist=cl)
    owner = UserFactory()
    draft = codelist_actions.export_to_builder(version=converted_clv, owner=owner)
    search_results = do_search(cl.coding_system, "elbow")
    actions.create_search(draft=draft, term="elbow", codes=search_results["all_codes"])

    client.force_login(owner)

    rsp = client.get(draft.get_builder_url("draft"))

    assert rsp.status_code == 200
    assert b"Test Codelist" in rsp.content


def test_search(client, tennis_elbow_codelist):
    cl = tennis_elbow_codelist
    converted_clv = codelist_actions.convert_codelist_to_new_style(codelist=cl)
    owner = UserFactory()
    draft = codelist_actions.export_to_builder(version=converted_clv, owner=owner)
    search_results = do_search(cl.coding_system, "elbow")
    actions.create_search(draft=draft, term="elbow", codes=search_results["all_codes"])

    client.force_login(owner)

    rsp = client.get(draft.get_builder_url("search", "elbow"))

    assert rsp.status_code == 200
    assert b'Search term: "elbow"' in rsp.content


def test_no_search_term(client, tennis_elbow_codelist):
    cl = tennis_elbow_codelist
    converted_clv = codelist_actions.convert_codelist_to_new_style(codelist=cl)
    owner = UserFactory()
    draft = codelist_actions.export_to_builder(version=converted_clv, owner=owner)
    search_results = do_search(cl.coding_system, "elbow")
    actions.create_search(draft=draft, term="elbow", codes=search_results["all_codes"])

    client.force_login(owner)

    rsp = client.get(draft.get_builder_url("no-search-term"))

    assert rsp.status_code == 200
    assert b"No search term" in rsp.content
