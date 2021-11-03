from codelists.tests.views.assertions import (
    assert_post_unauthenticated,
    assert_post_unauthorised,
)
from opencodelists.tests.assertions import assert_difference


def test_draft_with_no_searches(client, draft_with_no_searches):
    rsp = client.get(draft_with_no_searches.get_builder_draft_url())

    assert rsp.status_code == 200
    assert b"New-style Codelist" in rsp.content


def test_draft_with_some_searches(client, draft_with_some_searches):
    rsp = client.get(draft_with_some_searches.get_builder_draft_url())

    assert rsp.status_code == 200
    assert b"New-style Codelist" in rsp.content


def test_draft_with_complete_searches(client, draft_with_complete_searches):
    rsp = client.get(draft_with_complete_searches.get_builder_draft_url())

    assert rsp.status_code == 200
    assert b"New-style Codelist" in rsp.content


def test_draft_from_scratch(client, draft_from_scratch):
    rsp = client.get(draft_from_scratch.get_builder_draft_url())

    assert rsp.status_code == 200
    assert b"Codelist From Scratch" in rsp.content


def test_search(client, draft_with_some_searches):
    rsp = client.get(draft_with_some_searches.get_builder_search_url("arthritis"))

    assert rsp.status_code == 200
    assert rsp.context["results_heading"] == 'Showing concepts matching "arthritis"'


def test_no_search_term(client, draft_with_some_searches):
    rsp = client.get(draft_with_some_searches.get_builder_no_search_term_url())

    assert rsp.status_code == 200
    assert (
        rsp.context["results_heading"]
        == "Showing concepts with no matching search term"
    )


def test_post_unauthorised(client, draft):
    assert_post_unauthorised(client, draft.get_builder_draft_url())


def test_post_unauthenticated(client, draft):
    assert_post_unauthenticated(client, draft.get_builder_draft_url())


def test_post_save_for_review(client, draft):
    client.force_login(draft.draft_owner)

    rsp = client.post(
        draft.get_builder_draft_url(), {"action": "save-for-review"}, follow=True
    )
    assert rsp.redirect_chain[-1][0] == draft.get_absolute_url()

    draft.refresh_from_db()
    assert draft.is_under_review


def test_update_unauthorised(client, draft):
    assert_post_unauthorised(client, draft.get_builder_update_url())


def test_update_unauthenticated(client, draft):
    assert_post_unauthenticated(client, draft.get_builder_update_url())


def test_update(client, draft):
    client.force_login(draft.draft_owner)

    rsp = client.post(
        draft.get_builder_update_url(),
        {"updates": [("239964003", "-")]},
        "application/json",
    )

    draft.refresh_from_db()
    assert rsp.status_code == 200
    assert draft.code_objs.get(code=239964003).status == "-"


def test_new_search_unauthorised(client, draft):
    assert_post_unauthorised(client, draft.get_builder_new_search_url())


def test_new_search_unauthenticated(client, draft):
    assert_post_unauthenticated(client, draft.get_builder_new_search_url())


def test_new_search_for_term(client, draft):
    client.force_login(draft.draft_owner)

    with assert_difference(draft.searches.count, expected_difference=1):
        rsp = client.post(
            draft.get_builder_new_search_url(),
            {"search": "epicondylitis"},
            follow=True,
        )

    assert rsp.status_code == 200
    assert rsp.redirect_chain[-1][0] == draft.get_builder_search_url("epicondylitis")


def test_new_search_for_code(client, draft):
    client.force_login(draft.draft_owner)

    with assert_difference(draft.searches.count, expected_difference=1):
        rsp = client.post(
            draft.get_builder_new_search_url(),
            {"search": "code:128133004"},
            follow=True,
        )

    assert rsp.status_code == 200
    assert rsp.redirect_chain[-1][0] == draft.get_builder_search_url("code:128133004")


def test_new_search_no_results(client, draft):
    client.force_login(draft.draft_owner)

    with assert_difference(draft.searches.count, expected_difference=1):
        rsp = client.post(
            draft.get_builder_new_search_url(),
            {"search": "bananas"},
            follow=True,
        )

    assert rsp.status_code == 200
    assert b"bananas" in rsp.content
