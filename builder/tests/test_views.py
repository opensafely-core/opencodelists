import pytest
from django.urls import reverse

from codelists.actions import create_codelist_from_scratch
from codelists.models import Codelist
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


def test_version_from_scratch(client, version_from_scratch):
    rsp = client.get(version_from_scratch.get_builder_draft_url())

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
    client.force_login(draft.author)

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
    client.force_login(draft.author)

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
    client.force_login(draft.author)

    with assert_difference(draft.searches.count, expected_difference=1):
        rsp = client.post(
            draft.get_builder_new_search_url(),
            {"search": "epicondylitis"},
            follow=True,
        )

    assert rsp.status_code == 200
    assert rsp.redirect_chain[-1][0] == draft.get_builder_search_url("epicondylitis")


def test_new_search_for_code(client, draft):
    client.force_login(draft.author)

    with assert_difference(draft.searches.count, expected_difference=1):
        rsp = client.post(
            draft.get_builder_new_search_url(),
            {"search": "code:128133004"},
            follow=True,
        )

    assert rsp.status_code == 200
    assert rsp.redirect_chain[-1][0] == draft.get_builder_search_url("code:128133004")


def test_new_search_no_results(client, draft):
    client.force_login(draft.author)

    with assert_difference(draft.searches.count, expected_difference=1):
        rsp = client.post(
            draft.get_builder_new_search_url(),
            {"search": "bananas"},
            follow=True,
        )

    assert rsp.status_code == 200
    assert b"bananas" in rsp.content


@pytest.mark.parametrize(
    "term,slug,valid",
    [
        # standard characters with case
        ("Foo", "foo", True),
        # spaces and non-slug characters allowed, removed/replaced in slug
        ("foo 123", "foo-123", True),
        ("foo_123", "foo_123", True),
        ("&123", "123", True),
        # code: prefixed terms are not slugified
        ("code:*", "code:*", True),
        ("code:&£%^", "code:&£%^", True),
        # search terms that result in an empty slug are not allowed
        ("*", "", False),
        ("&£%^", "", False),
    ],
)
def test_new_search_check_slugified_terms(client, draft, term, valid, slug):
    client.force_login(draft.author)

    rsp = client.post(
        draft.get_builder_new_search_url(),
        {"search": term},
    )
    assert rsp.status_code == 302
    if valid:
        assert rsp.url == draft.get_builder_search_url(slug)
    else:
        assert rsp.url == draft.get_absolute_url()


def test_discard_only_draft_version(client, organisation_user):
    new_codelist = create_codelist_from_scratch(
        owner=organisation_user,
        author=organisation_user,
        name="foo",
        coding_system_id="snomedct",
    )
    assert new_codelist.versions.count() == 1
    draft = new_codelist.versions.first()

    client.force_login(organisation_user)

    rsp = client.post(draft.get_builder_draft_url(), {"action": "discard"}, follow=True)
    assert rsp.status_code == 200

    # Codelist was deleted along with its only draft; redirects to user's codelists page
    assert Codelist.objects.filter(id=new_codelist.id).exists() is False
    assert rsp.redirect_chain[-1][0] == reverse(
        "user", args=(organisation_user.username,)
    )


def test_discard_one_draft_version(client, draft):
    assert draft.codelist.versions.count() > 1
    client.force_login(draft.author)

    rsp = client.post(draft.get_builder_draft_url(), {"action": "discard"}, follow=True)
    assert rsp.status_code == 200
    # As more than one version existed, the codelist still exists; redirects to the codelist's
    # absolute url, which in turn redirects to the latest visible version
    assert rsp.redirect_chain[-2][0] == draft.codelist.get_absolute_url()
    assert (
        rsp.redirect_chain[-1][0]
        == draft.codelist.latest_visible_version(draft.author).get_absolute_url()
    )
