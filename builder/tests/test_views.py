def test_draft_with_no_searches(client, draft_with_no_searches):
    client.force_login(draft_with_no_searches.draft_owner)
    rsp = client.get(draft_with_no_searches.get_builder_url("draft"))

    assert rsp.status_code == 200
    assert b"New-style Codelist" in rsp.content


def test_draft_with_some_searches(client, draft_with_some_searches):
    client.force_login(draft_with_some_searches.draft_owner)
    rsp = client.get(draft_with_some_searches.get_builder_url("draft"))

    assert rsp.status_code == 200
    assert b"New-style Codelist" in rsp.content


def test_draft_with_complete_searches(client, draft_with_complete_searches):
    client.force_login(draft_with_complete_searches.draft_owner)
    rsp = client.get(draft_with_complete_searches.get_builder_url("draft"))

    assert rsp.status_code == 200
    assert b"New-style Codelist" in rsp.content


def test_version_from_scratch(client, version_from_scratch):
    client.force_login(version_from_scratch.draft_owner)
    rsp = client.get(version_from_scratch.get_builder_url("draft"))

    assert rsp.status_code == 200
    assert b"Codelist From Scratch" in rsp.content


def test_search(client, draft_with_some_searches):
    client.force_login(draft_with_some_searches.draft_owner)
    rsp = client.get(draft_with_some_searches.get_builder_url("search", "arthritis"))

    assert rsp.status_code == 200
    assert rsp.context["results_heading"] == 'Showing concepts matching "arthritis"'


def test_no_search_term(client, draft_with_some_searches):
    client.force_login(draft_with_some_searches.draft_owner)
    rsp = client.get(draft_with_some_searches.get_builder_url("no-search-term"))

    assert rsp.status_code == 200
    assert (
        rsp.context["results_heading"]
        == "Showing concepts with no matching search term"
    )
