import pytest
from django.core.exceptions import ObjectDoesNotExist

from builder import actions
from opencodelists.tests.assertions import assert_difference


def test_create_search(version_from_scratch):
    draft = version_from_scratch

    # Act: create a term search
    s = actions.create_search(
        draft=draft,
        term="epicondylitis",
        codes={"73583000", "202855006"},
    )

    # Assert...
    # that the search's attributes have been set
    assert s.version == draft
    assert s.term == "epicondylitis"
    assert s.code is None
    assert s.slug == "epicondylitis"

    # that the newly created search has 2 results
    assert s.results.count() == 2
    # that the draft has 1 search
    assert draft.searches.count() == 1
    # that the draft has 2 codes
    assert draft.code_objs.count() == 2

    # Act: create a code search
    s = actions.create_search(draft=draft, code="73583000", codes=["73583000"])

    # Assert...
    # that the search's attributes have been set
    assert s.version == draft
    assert s.term is None
    assert s.code == "73583000"
    assert s.slug == "code:73583000"

    # that the newly created search has 1 result
    assert s.results.count() == 1
    # that the codelist has 2 searches
    assert draft.searches.count() == 2
    # that the codelist still has 2 codes, since the code search returns a code that was
    # returned by the term search
    assert draft.code_objs.count() == 2


def test_duplicate_search(version_from_scratch):
    # Test that a user can search for the same term again without error

    draft = version_from_scratch

    # Act: create a term search
    s = actions.create_search(
        draft=draft,
        term="epicondylitis",
        codes={"73583000", "202855006"},
    )

    # Assert...
    # that the search's attributes have been set
    assert s.version == draft
    assert s.term == "epicondylitis"
    assert s.code is None
    assert s.slug == "epicondylitis"

    # that the newly created search has 2 results
    assert s.results.count() == 2
    # that the draft has 1 search
    assert draft.searches.count() == 1
    # that the draft has 2 codes
    assert draft.code_objs.count() == 2

    # try to repeat the same search
    s1 = actions.create_search(
        draft=draft,
        term="epicondylitis",
        codes={"73583000", "202855006"},
    )

    # Assert...
    # that the initally created search was returned
    assert s1.id == s.id

    # that the draft still has the same search and code counts
    assert draft.searches.count() == 1
    assert draft.code_objs.count() == 2


@pytest.mark.xfail
def test_delete_search():
    pass
    # # Arrange: create a draft with codes and a search
    # codelist = CodelistFactory()
    # owner = UserFactory()
    # draft = actions.create_draft_with_codes(
    #     codelist=codelist,
    #     owner=owner,
    #     codes=["1067731000000107", "1068181000000106"],
    # )
    # s = actions.create_search(
    #     draft=draft, term="synchronised", codes=["1068181000000106"]
    # )

    # # Act: delete the search
    # actions.delete_search(search=s)

    # # Assert...
    # # that the codelist has 0 searches
    # assert draft.searches.count() == 0
    # # that the still codelist has 1 code which doesn't belong to a search
    # assert draft.code_objs.count() == 1

    # # Arrange: create new searches
    # s1 = actions.create_search(
    #     draft=draft, term="synchronised", codes=["1068181000000106"]
    # )
    # s2 = actions.create_search(
    #     draft=draft, term="swimming", codes=["1067731000000107", "1068181000000106"]
    # )

    # # Act: delete the search for "swimming"
    # actions.delete_search(search=s2)

    # # Assert...
    # # that the codelist has only 1 search
    # assert draft.searches.count() == 1
    # # that the codelist has only 1 code
    # assert draft.code_objs.count() == 1

    # # Arrange: recreate the search for "swimming"
    # actions.create_search(
    #     draft=draft, term="swimming", codes=["1067731000000107", "1068181000000106"]
    # )

    # # Act: delete the search for "synchronised"
    # actions.delete_search(search=s1)

    # # Assert...
    # # that the codelist has only 1 search
    # assert draft.searches.count() == 1
    # # that the codelist still has both codes
    # assert draft.code_objs.count() == 2


def test_update_code_statuses(draft_with_no_searches):
    draft = draft_with_no_searches
    # Double check that codes and statuses are as expected
    assert dict(draft.code_objs.values_list("code", "status")) == {
        "128133004": "+",  # Disorder of elbow
        "429554009": "(+)",  # Arthropathy of elbow
        "35185008": "(+)",  # Enthesopathy of elbow region
        "73583000": "(+)",  # Epicondylitis
        "239964003": "(+)",  # Soft tissue lesion of elbow region
        "439656005": "-",  # Arthritis of elbow
        "202855006": "(-)",  # Lateral epicondylitis
        "156659008": "+",  # (Epicondylitis &/or ...
    }

    # Act: process single update from the client
    actions.update_code_statuses(draft=draft, updates=[("156659008", "?")])

    # Assert that results have the expected status
    assert dict(draft.code_objs.values_list("code", "status")) == {
        "128133004": "+",  # Disorder of elbow
        "429554009": "(+)",  # Arthropathy of elbow
        "35185008": "(+)",  # Enthesopathy of elbow region
        "73583000": "(+)",  # Epicondylitis
        "239964003": "(+)",  # Soft tissue lesion of elbow region
        "439656005": "-",  # Arthritis of elbow
        "202855006": "(-)",  # Lateral epicondylitis
        "156659008": "?",  # (Epicondylitis &/or ...
    }

    # Act: process multiple updates from the client
    actions.update_code_statuses(
        draft=draft,
        updates=[("439656005", "?"), ("128133004", "-"), ("156659008", "-")],
    )

    # Assert that results have the expected status
    assert dict(draft.code_objs.values_list("code", "status")) == {
        "128133004": "-",  # Disorder of elbow
        "429554009": "(-)",  # Arthropathy of elbow
        "35185008": "(-)",  # Enthesopathy of elbow region
        "73583000": "(-)",  # Epicondylitis
        "239964003": "(-)",  # Soft tissue lesion of elbow region
        "439656005": "(-)",  # Arthritis of elbow
        "202855006": "(-)",  # Lateral epicondylitis
        "156659008": "-",  # (Epicondylitis &/or ...
    }


def test_save(draft_with_no_searches):
    draft = draft_with_no_searches
    actions.save(draft=draft)
    draft.refresh_from_db()
    assert draft.draft_owner is None
    assert draft.is_under_review


def test_discard_draft(draft_with_complete_searches):
    codelist = draft_with_complete_searches.codelist
    with assert_difference(codelist.versions.count, expected_difference=-1):
        actions.discard_draft(draft=draft_with_complete_searches)
    with pytest.raises(ObjectDoesNotExist):
        draft_with_complete_searches.refresh_from_db()


def test_discard_draft_from_scratch(version_from_scratch):
    codelist = version_from_scratch.codelist
    actions.discard_draft(draft=version_from_scratch)
    with pytest.raises(ObjectDoesNotExist):
        codelist.refresh_from_db()
