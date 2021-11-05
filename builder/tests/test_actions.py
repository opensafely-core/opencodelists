import pytest
from django.core.exceptions import ObjectDoesNotExist

from builder import actions
from opencodelists.tests.assertions import assert_difference


def test_create_search(draft_from_scratch):
    draft = draft_from_scratch

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


def test_delete_search_1(draft_with_complete_searches):
    # In this test, we delete the searches belonging to a draft one by one, and check
    # that the number of remaining searches and code objects belonging to the draft are
    # as expected.
    #
    # Refer to the table in the module docstring of fixtures.py to understand where
    # the magic numbers below come from.

    draft = draft_with_complete_searches

    assert draft.searches.count() == 4
    assert draft.code_objs.count() == 13

    actions.delete_search(search=draft.searches.get(code="439656005"))
    assert draft.searches.count() == 3
    assert draft.code_objs.count() == 13

    actions.delete_search(search=draft.searches.get(term="arthritis"))
    assert draft.searches.count() == 2
    assert draft.code_objs.count() == 12

    actions.delete_search(search=draft.searches.get(term="elbow"))
    assert draft.searches.count() == 1
    assert draft.code_objs.count() == 3

    actions.delete_search(search=draft.searches.get(term="tennis"))
    assert draft.searches.count() == 0
    assert draft.code_objs.count() == 0


def test_delete_search_2(draft_with_some_searches):
    from django.db.models import Count
    from django.db.models.query import QuerySet
    from django_tabulate import tabulate_qs

    QuerySet.__repr__ = tabulate_qs

    draft = draft_with_some_searches
    print("A", "-" * 80)
    print(draft.code_objs.annotate(num_results=Count("results")))

    codes1 = set(co.code for co in draft.code_objs.all())

    assert draft.searches.count() == 1
    assert draft.code_objs.count() == 9

    actions.delete_search(search=draft.searches.get(term="arthritis"))
    assert draft.searches.count() == 0
    # assert draft.code_objs.count() == 6

    print("B", "-" * 80)
    print(draft.code_objs.annotate(num_results=Count("results")))

    codes2 = set(co.code for co in draft.code_objs.all())

    print(codes1 - codes2)
    assert draft.code_objs.filter(code="202855006").exists()


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


def test_discard_draft_from_scratch(draft_from_scratch):
    codelist = draft_from_scratch.codelist
    actions.discard_draft(draft=draft_from_scratch)
    with pytest.raises(ObjectDoesNotExist):
        codelist.refresh_from_db()
