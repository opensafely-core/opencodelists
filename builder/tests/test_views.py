import pytest
from django.core.validators import MinLengthValidator
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from codelists.actions import create_codelist_from_scratch
from codelists.coding_systems import most_recent_database_alias
from codelists.models import Codelist, Search
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
    slug = "arthritis"
    search = draft_with_some_searches.searches.filter(term=slug).first()
    search_id = search.id

    num_concepts = len(search.results.values_list("code_obj__code", flat=True))

    rsp = client.get(draft_with_some_searches.get_builder_search_url(search_id, slug))

    assert rsp.status_code == 200
    assert (
        rsp.context["results_heading"]
        == f'Showing {num_concepts} concepts matching "{slug}"'
    )


def test_search_non_int_search_id(client, draft_with_some_searches):
    """Test that the URL dispatcher can't call the search view with a
    non-integer string as `search_id`."""
    slug = "arthritis"
    search_id = "bad_search_id"

    with pytest.raises(NoReverseMatch):
        client.get(draft_with_some_searches.get_builder_search_url(search_id, slug))


def test_no_search_term(client, draft_with_some_searches):
    rsp = client.get(draft_with_some_searches.get_builder_no_search_term_url())
    num_concepts = len(
        draft_with_some_searches.code_objs.filter(results=None).values_list(
            "code", flat=True
        )
    )

    assert rsp.status_code == 200
    assert (
        rsp.context["results_heading"]
        == f"Showing {num_concepts} concepts with no matching search term"
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
            {"search": "epicondylitis", "search-type": "term"},
            follow=True,
        )

    assert rsp.status_code == 200
    last_search_id = draft.searches.last().id
    assert rsp.redirect_chain[-1][0] == draft.get_builder_search_url(
        last_search_id, "epicondylitis"
    )


def test_new_search_for_code(client, draft):
    client.force_login(draft.author)

    with assert_difference(draft.searches.count, expected_difference=1):
        rsp = client.post(
            draft.get_builder_new_search_url(),
            {"search": "128133004", "search-type": "code"},
            follow=True,
        )

    assert rsp.status_code == 200
    last_search_id = draft.searches.last().id
    assert rsp.redirect_chain[-1][0] == draft.get_builder_search_url(
        last_search_id, "code:128133004"
    )


def test_new_search_no_results(client, draft):
    client.force_login(draft.author)

    with assert_difference(draft.searches.count, expected_difference=1):
        rsp = client.post(
            draft.get_builder_new_search_url(),
            {"search": "bananas", "search-type": "term"},
            follow=True,
        )

    assert rsp.status_code == 200
    assert b"bananas" in rsp.content


def test_new_search_first_non_alphanumeric_second_normal(
    client, draft_with_no_searches
):
    client.force_login(draft_with_no_searches.author)

    num_codes_before = len(draft_with_no_searches.codeset.all_codes())
    # The string with the non-alphanumeric character doesn't return any
    # matches, but it should still be counted as a search
    with assert_difference(
        draft_with_no_searches.searches.count, expected_difference=1
    ):
        client.post(
            draft_with_no_searches.get_builder_new_search_url(),
            {"search": "epicondylitis*", "search-type": "term"},
            follow=True,
        )

    # We expect the first search to return no codes
    assert len(draft_with_no_searches.codeset.all_codes()) == num_codes_before

    # The second search without the non-alphanumric chars should still be
    # classed as a search, even though the slug is the same
    with assert_difference(
        draft_with_no_searches.searches.count, expected_difference=1
    ):
        client.post(
            draft_with_no_searches.get_builder_new_search_url(),
            {"search": "epicondylitis", "search-type": "term"},
            follow=True,
        )

    # This search returns should have returned some codes
    assert len(draft_with_no_searches.codeset.all_codes()) > num_codes_before


def test_new_search_first_normal_second_non_alphanumeric(
    client, draft_with_no_searches
):
    client.force_login(draft_with_no_searches.author)

    num_codes_before = len(draft_with_no_searches.codeset.all_codes())
    with assert_difference(
        draft_with_no_searches.searches.count, expected_difference=1
    ):
        client.post(
            draft_with_no_searches.get_builder_new_search_url(),
            {"search": "epicondylitis", "search-type": "term"},
            follow=True,
        )

    # We expect the first search to return codes
    num_codes_after = len(draft_with_no_searches.codeset.all_codes())
    assert num_codes_after > num_codes_before

    # The second search with the non-alphanumric chars should still be
    # classed as a search, even though the slug is the same
    with assert_difference(
        draft_with_no_searches.searches.count, expected_difference=1
    ):
        client.post(
            draft_with_no_searches.get_builder_new_search_url(),
            {"search": "epicondylitis*", "search-type": "term"},
            follow=True,
        )

    # The last search returns no codes, so the number shouldn't have changed
    assert num_codes_after == len(draft_with_no_searches.codeset.all_codes())


@pytest.mark.parametrize(
    "term,search_type,slug,valid",
    [
        # standard characters with case
        ("Foo", "term", "foo", True),
        # spaces and non-slug characters allowed, removed/replaced in slug
        ("foo 123", "term", "foo-123", True),
        ("foo_123", "term", "foo_123", True),
        ("&123", "term", "123", True),
        # code searches gain a "code:" prefix but remain unchanged
        ("123", "code", "code:123", True),
        ("12 34", "code", "code:12 34", True),
        # search terms that result in an empty slug are not allowed
        ("*", "term", "", False),
        ("&£%^", "term", "", False),
    ],
)
def test_new_search_check_slugified_terms(
    client, draft, term, search_type, valid, slug
):
    client.force_login(draft.author)

    rsp = client.post(
        draft.get_builder_new_search_url(),
        {"search": term, "search-type": search_type},
    )
    assert rsp.status_code == 302
    last_search_id = draft.searches.last().id
    last_search_slug = draft.searches.last().slug
    if valid:
        assert slug == last_search_slug
        assert rsp.url == draft.get_builder_search_url(last_search_id, last_search_slug)
    else:
        assert rsp.url == draft.get_builder_draft_url()


def test_discard_only_draft_version(client, organisation_user):
    new_codelist = create_codelist_from_scratch(
        owner=organisation_user,
        author=organisation_user,
        name="foo",
        coding_system_id="snomedct",
        coding_system_database_alias=most_recent_database_alias("snomedct"),
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


def test_max_search_length_validation(client, draft_with_no_searches):
    client.force_login(draft_with_no_searches.author)

    max_search_term_length = Search._meta.get_field("term").max_length
    term_with_max_chars = "a" * max_search_term_length
    term_with_too_many_chars = "a" * (max_search_term_length + 1)
    expected_term_error = (
        f"Ensure this value has at most {max_search_term_length} characters".encode()
    )

    # If the search term length is at the limit then it is a valid search so the
    # search count increments by one and the error message is not in the response
    with assert_difference(
        draft_with_no_searches.searches.count, expected_difference=1
    ):
        rsp = client.post(
            draft_with_no_searches.get_builder_new_search_url(),
            {"search": term_with_max_chars, "search-type": "term"},
            follow=True,
        )
    assert rsp.status_code == 200
    assert expected_term_error not in rsp.content

    # If the search term length is over the limit then it is an invalid search so
    # the search count does not increment and the error message is in the response
    with assert_difference(
        draft_with_no_searches.searches.count, expected_difference=0
    ):
        rsp = client.post(
            draft_with_no_searches.get_builder_new_search_url(),
            {"search": term_with_too_many_chars, "search-type": "term"},
            follow=True,
        )
    assert rsp.status_code == 200
    assert expected_term_error in rsp.content

    max_search_code_length = Search._meta.get_field("code").max_length
    code_with_max_chars = "a" * max_search_code_length
    code_with_too_many_chars = "a" * (max_search_code_length + 1)
    expected_code_error = (
        f"Ensure this value has at most {max_search_code_length} characters".encode()
    )

    # If the search code length is at the limit then it is a valid search so the
    # search count increments by one and the error message is not in the response
    with assert_difference(
        draft_with_no_searches.searches.count, expected_difference=1
    ):
        rsp = client.post(
            draft_with_no_searches.get_builder_new_search_url(),
            {"search": code_with_max_chars, "search-type": "code"},
            follow=True,
        )
    assert rsp.status_code == 200
    assert expected_code_error not in rsp.content

    # If the search code length is over the limit then it is an invalid search so
    # the search count does not increment and the error message is in the response
    with assert_difference(
        draft_with_no_searches.searches.count, expected_difference=0
    ):
        rsp = client.post(
            draft_with_no_searches.get_builder_new_search_url(),
            {"search": code_with_too_many_chars, "search-type": "code"},
            follow=True,
        )
    assert rsp.status_code == 200
    assert expected_code_error in rsp.content


def get_validator_limit_value(validators, validator_class):
    """Takes a list of Django validator instances and
    returns the validator value for a specific class,
    asserting that there is a value and only one value."""
    limit_values = [
        validator.limit_value
        for validator in validators
        if isinstance(validator, validator_class)
    ]
    assert len(limit_values) == 1
    return limit_values[0]


def test_min_search_length_validation(client, draft_with_no_searches):
    client.force_login(draft_with_no_searches.author)

    term_field_validators = Search._meta.get_field("term").validators
    min_search_term_length = get_validator_limit_value(
        term_field_validators, MinLengthValidator
    )

    term_with_min_chars = "a" * min_search_term_length
    term_with_too_few_chars = "a" * (min_search_term_length - 1)
    expected_term_error = (
        f"Ensure this value has at least {min_search_term_length} characters".encode()
    )

    # If the search term length is at the limit then it is a valid search so the
    # search count increments by one and the error message is not in the response
    with assert_difference(
        draft_with_no_searches.searches.count, expected_difference=1
    ):
        rsp = client.post(
            draft_with_no_searches.get_builder_new_search_url(),
            {"search": term_with_min_chars, "search-type": "term"},
            follow=True,
        )
    assert rsp.status_code == 200
    assert expected_term_error not in rsp.content

    # If the search term length is under the limit then it is an invalid search so
    # the search count does not increment and the error message is in the response
    with assert_difference(
        draft_with_no_searches.searches.count, expected_difference=0
    ):
        rsp = client.post(
            draft_with_no_searches.get_builder_new_search_url(),
            {"search": term_with_too_few_chars, "search-type": "term"},
            follow=True,
        )
    assert rsp.status_code == 200
    assert expected_term_error in rsp.content

    code_field_validators = Search._meta.get_field("code").validators
    min_search_code_length = get_validator_limit_value(
        code_field_validators, MinLengthValidator
    )
    code_with_min_chars = "a" * min_search_code_length
    expected_code_error = (
        f"Ensure this value has at least {min_search_code_length} characters".encode()
    )

    # If the search code length is at the limit then it is a valid search so the
    # search count increments by one and the error message is not in the response
    with assert_difference(
        draft_with_no_searches.searches.count, expected_difference=1
    ):
        rsp = client.post(
            draft_with_no_searches.get_builder_new_search_url(),
            {"search": code_with_min_chars, "search-type": "code"},
            follow=True,
        )
    assert rsp.status_code == 200
    assert expected_code_error not in rsp.content

    # Note: The current minimum search code length is 1.
    # Below is an assertion to validate this.
    # A minimum search code length of 1 means the value
    # below the minimum is zero.
    # What happens if we enter a search below the minimum
    # code length is that we encounter the case where
    # no search is entered. That case is handled differently
    # by new_search() to guard against searches
    # that cannot be slugified.
    # We do not reach the Django MinValidationError,
    # unlike for terms.
    assert len(code_with_min_chars) == 1


def test_search_delete(client, minimal_draft):
    """Test that a POST to the `delete_search` view deletes the selected
    search, and redirects to the draft view."""
    client.force_login(minimal_draft.author)

    term = "tennis toe"
    slug = "tennis-toe"
    searches = minimal_draft.searches.all()
    # Two search terms pre-populated in fixture.
    assert {s.term for s in searches} == {"tennis toe", "enthesopathy of elbow"}

    search = searches.filter(term=term).first()
    rsp = client.post(minimal_draft.get_builder_delete_search_url(search.id, slug))

    # Redirected to draft.
    assert rsp.status_code == 302
    assert rsp.url == minimal_draft.get_builder_draft_url()

    # Search was deleted.
    updated_searches = minimal_draft.searches.all()
    assert {s.term for s in updated_searches} == {"enthesopathy of elbow"}


def test_search_delete_get(client, minimal_draft):
    """Test that a GET to the `delete_search` view is not permitted."""
    client.force_login(minimal_draft.author)

    term = "tennis toe"
    slug = "tennis-toe"
    searches = minimal_draft.searches.all()
    search = searches.filter(term=term).first()

    rsp = client.get(minimal_draft.get_builder_delete_search_url(search.id, slug))

    # 405 Method not allowed.
    assert rsp.status_code == 405


def test_search_delete_non_int_search_id(client, minimal_draft):
    """Test that the URL dispatcher can't call the `delete_search` view with a
    non-integer string as `search_id`."""
    client.force_login(minimal_draft.author)

    slug = "tennis-toe"
    search_id = "bad_search_id"

    with pytest.raises(NoReverseMatch):
        client.post(minimal_draft.get_builder_delete_search_url(search_id, slug))


def test_max_length_description(client, draft_with_some_searches):
    from codelists.forms import description_max_length

    client.force_login(draft_with_some_searches.author)

    rsp = client.get(draft_with_some_searches.get_builder_draft_url())
    assert f'max_length": {description_max_length}'.encode() in rsp.content


# Test that existing long descriptions can be edited and saved
def test_edit_long_description(client, draft_with_some_searches):
    from codelists.forms import description_max_length

    client.force_login(draft_with_some_searches.author)

    # Set a longer than max_length description (for legacy codelists)
    long_description = "A" * (description_max_length + 1)
    draft_with_some_searches.codelist.description = long_description
    draft_with_some_searches.codelist.save()

    # Check that the description is set correctly
    assert draft_with_some_searches.codelist.description == long_description

    # The description is already longer than max_length characters, so the
    # max_length attribute should not be present in the form field.
    rsp = client.get(draft_with_some_searches.get_builder_draft_url())
    assert rsp.status_code == 200
    assert f'max_length": {description_max_length}'.encode() not in rsp.content

    # Updating the description to a new longer than allowed value is ok
    new_description = "B" * (description_max_length + 1)
    client.post(
        draft_with_some_searches.get_builder_update_url(),
        {"description": new_description},
        "application/json",
        follow=True,
    )

    # The max_length attribute should still not be present
    rsp = client.get(draft_with_some_searches.get_builder_draft_url())
    assert rsp.status_code == 200
    assert f'max_length": {description_max_length}'.encode() not in rsp.content

    # Now we update to a description that is a valid length
    new_description = "B" * (description_max_length)
    client.post(
        draft_with_some_searches.get_builder_update_url(),
        {"description": new_description},
        "application/json",
        follow=True,
    )

    # This time the max_length attribute should be present
    rsp = client.get(draft_with_some_searches.get_builder_draft_url())
    assert rsp.status_code == 200
    assert f'max_length": {description_max_length}'.encode() in rsp.content
