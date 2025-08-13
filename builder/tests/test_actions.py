import pytest
from django.core.exceptions import ObjectDoesNotExist

from builder import actions
from codelists.models import Search
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


def test_quasi_duplicate_search(version_from_scratch):
    # Test that a user can search for terms that only differ
    # by non-alphanumeric characters

    draft = version_from_scratch

    ac_code_1 = "1028271000000109"
    ac_code_2 = "1023491000000104"
    ac_code_3 = "1027791000000103"
    ac_code_4 = "250745003"

    # Act: create a term search
    s = actions.create_search(
        draft=draft,
        term="albumin / creatinine",
        codes={ac_code_1, ac_code_2, ac_code_3},
    )

    # check we have 1 search with 3 codes
    assert draft.searches.count() == 1
    assert draft.code_objs.count() == 3

    # do a search which is identical ignoring non-alphanumeric characters
    # and stripping white space to single spaces
    s1 = actions.create_search(
        draft=draft,
        term="albumin creatinine",
        codes={ac_code_1, ac_code_4},
    )

    # Assert...
    # that a new search was returned
    assert s1.id != s.id

    # that the draft now has two searches with 4 codes in total
    assert draft.searches.count() == 2
    assert draft.code_objs.count() == 4


def test_delete_search(version_from_scratch):
    draft = version_from_scratch

    # Act: create a term search
    s = actions.create_search(
        draft=draft,
        term="epicondylitis",
        codes={"73583000", "202855006"},
    )

    # Act: delete the search
    actions.delete_search(search=s)

    # Assert...
    # that the codelist has 0 searches
    assert draft.searches.count() == 0
    # that the codelist has no codes
    assert draft.code_objs.count() == 0

    # Arrange: create new searches
    s1 = actions.create_search(
        draft=draft,
        term="epicondylitis",
        codes={"73583000", "202855006"},
    )
    s2 = actions.create_search(
        draft=draft, term="Soft tissue lesion", codes={"239964003"}
    )
    # This search also returns the codes from s1
    s3 = actions.create_search(
        draft=draft,
        term="Enthesopathy of elbow region",
        codes={"35185008", "73583000", "202855006"},
    )

    # Act: delete the search for "Soft tissue lesion"
    actions.delete_search(search=s2)

    # Assert...
    # that the codelist has 2 searches
    assert draft.searches.count() == 2
    # that the codelist has 3 codes
    assert draft.code_objs.count() == 3

    # Act: delete the search for "Enthesopathy of elbow region"
    actions.delete_search(search=s3)

    # Assert...
    # that the codelist has only 1 search
    assert draft.searches.count() == 1
    # that the codelist now has 2 codes; although codes 73583000 and 202855006 are
    # in the search for "Enthesopathy of elbow region", they are not deleted because
    # the are also in the search for "epicondylitis"
    assert draft.code_objs.count() == 2

    # Act: delete the remainng search for "epicondylitis"
    actions.delete_search(search=s1)
    assert draft.searches.count() == 0
    assert draft.code_objs.count() == 0


def test_delete_search_codelist_with_codes(version_with_no_searches):
    draft = version_with_no_searches
    codelist_codes = draft.codeset.all_codes()
    included_codes = draft.codeset.codes()
    assert len(codelist_codes) == 8
    assert len(included_codes) == 6

    # This codelist has all the codes for disorder of elbow excluding arthritis
    # 8 codes, 6 included
    """
                        + 128133004 Disorder of elbow
                                        |
         --------------- --------------- -----------------------           Inactive (hence orphaned) code
        |                               |                       |                   |
    + 429554009                     + 35185008              + 239964003           + 156659008
    Arthropathy of elbow          Enthesopathy of       Soft tissue lesion     (Epicondylitis &/or tennis elbow)
        |                           elbow region          of elbow region       or (golfers' elbow) [inactive]
        |                               |
    - 439656005                     + 73583000
    Arthritis of elbow            Epicondylitis
        |                               |
        -----------202855006-------------
              - Lateral epicondylitis
    """
    # Epicondylitis codes are already included on the codelist; one is included, one is not
    epicondylitis_included_code = "73583000"
    epicondylitis_excluded_code = "202855006"
    epicondylitis_codes = {epicondylitis_included_code, epicondylitis_excluded_code}
    # Tennis toe code is not on the codelist
    tennis_toe_code = "238484001"

    # Arthritis of elbow is on the codelist, but not included
    arthritis_of_elbow_codes = {"439656005", "202855006"}

    assert epicondylitis_included_code in included_codes
    assert epicondylitis_excluded_code not in included_codes
    for code in epicondylitis_codes:
        assert code in codelist_codes
    assert tennis_toe_code not in codelist_codes
    assert tennis_toe_code not in included_codes
    for code in arthritis_of_elbow_codes:
        assert code in codelist_codes
        assert code not in included_codes

    # Act: create a term search
    s = actions.create_search(
        draft=draft,
        term="Tennis toe",
        codes={tennis_toe_code},
    )

    # Act: delete the search
    actions.delete_search(search=s)

    # Assert...
    # that the codelist has 0 searches
    assert draft.searches.count() == 0
    # that the codelist still has the codes that were not associated with the search
    assert draft.code_objs.count() == len(codelist_codes)

    # Arrange: create new searches
    s1 = actions.create_search(
        draft=draft,
        term="epicondylitis",
        codes=epicondylitis_codes,
    )
    s2 = actions.create_search(draft=draft, term="Tennis toe", codes={tennis_toe_code})

    # Assert...
    # that the codelist now has 2 searches
    assert draft.searches.count() == 2
    # and one extra code obj
    assert draft.code_objs.count() == len(codelist_codes) + 1

    # Act: include the Tennis toe code; this has no ancestors on the codelist
    actions.update_code_statuses(draft=draft, updates=[(tennis_toe_code, "+")])

    # Act: delete the search for "Tennis toe"
    actions.delete_search(search=s2)

    # Assert...
    # that the codelist has only 1 search
    assert draft.searches.count() == 1
    # that the codelist still has the starting codes that were not associated with the search
    # AND the tennis toe code that was included
    assert draft.code_objs.count() == len(codelist_codes) + 1

    # Arrange
    # Recreate the search for tennis toe and make it unresolved
    actions.update_code_statuses(draft=draft, updates=[(tennis_toe_code, "?")])
    s2 = actions.create_search(draft=draft, term="Tennis toe", codes={tennis_toe_code})

    # Act: delete the search for "Tennis toe"
    actions.delete_search(search=s2)
    # Assert...
    # that the codelist has only 1 search
    assert draft.searches.count() == 1
    # that the codelist still has the starting codes that were not associated with the search
    # but this time the tennis toe code was deleted because it wasn't included
    assert draft.code_objs.count() == len(codelist_codes)

    # Act: delete the search for "epicondylitis"
    actions.delete_search(search=s1)

    # Assert...
    # that the codelist has no searches
    assert draft.searches.count() == 0
    # This search matched 2 codes, one included, one not included, but a descendant of an included
    # code, they are not deleted
    assert draft.code_objs.count() == len(codelist_codes)

    # Arrange: create new search for not-included code
    s3 = actions.create_search(
        draft=draft,
        term="arthritis of elbow",
        codes=arthritis_of_elbow_codes,
    )

    # Act: delete the search for "arthritis of elbow"
    actions.delete_search(search=s3)

    # Assert...
    # that the codelist has no searches
    assert draft.searches.count() == 0
    # The code is not included, but it is a descendant of an included search, so it is kept
    assert draft.code_objs.count() == len(codelist_codes)


def test_update_code_statuses(draft_with_complete_searches):
    draft = draft_with_complete_searches
    codes_that_dont_change = {
        "3723001": "-",
        "238484001": "-",
        "298869002": "(-)",
        "116309007": "-",
        "298163003": "(-)",
    }
    # Double check that codes and statuses are as expected
    assert (
        dict(draft.code_objs.values_list("code", "status"))
        == {
            "128133004": "+",  # Disorder of elbow
            "429554009": "(+)",  # Arthropathy of elbow
            "35185008": "(+)",  # Enthesopathy of elbow region
            "73583000": "(+)",  # Epicondylitis
            "239964003": "(+)",  # Soft tissue lesion of elbow region
            "439656005": "+",  # Arthritis of elbow
            "202855006": "(+)",  # Lateral epicondylitis
            "156659008": "+",  # (Epicondylitis &/or ...
        }
        | codes_that_dont_change
    )
    actions.update_code_statuses(draft=draft, updates=[("439656005", "-")])
    assert (
        dict(draft.code_objs.values_list("code", "status"))
        == {
            "128133004": "+",  # Disorder of elbow
            "429554009": "(+)",  # Arthropathy of elbow
            "35185008": "(+)",  # Enthesopathy of elbow region
            "73583000": "(+)",  # Epicondylitis
            "239964003": "(+)",  # Soft tissue lesion of elbow region
            "439656005": "-",  # Arthritis of elbow
            "202855006": "(-)",  # Lateral epicondylitis
            "156659008": "+",  # (Epicondylitis &/or ...
        }
        | codes_that_dont_change
    )

    # Act: process single update from the client
    actions.update_code_statuses(draft=draft, updates=[("156659008", "?")])

    # Assert that results have the expected status
    assert (
        dict(draft.code_objs.values_list("code", "status"))
        == {
            "128133004": "+",  # Disorder of elbow
            "429554009": "(+)",  # Arthropathy of elbow
            "35185008": "(+)",  # Enthesopathy of elbow region
            "73583000": "(+)",  # Epicondylitis
            "239964003": "(+)",  # Soft tissue lesion of elbow region
            "439656005": "-",  # Arthritis of elbow
            "202855006": "(-)",  # Lateral epicondylitis
            "156659008": "?",  # (Epicondylitis &/or ...
        }
        | codes_that_dont_change
    )

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
        "3723001": "-",
        "238484001": "-",
        "298869002": "(-)",
        "116309007": "-",
        "298163003": "(-)",
    }


def test_orphaned_code_behaviour(draft_with_some_searches):
    draft = draft_with_some_searches

    # Double check that codes and statuses are as expected
    assert dict(draft.code_objs.values_list("code", "status")) == {
        # Part of arthritis search
        "439656005": "+",  # Arthritis of elbow
        "202855006": "(+)",  # Lateral epicondylitis
        "3723001": "-",  # Arthritis
        # Orphans
        "128133004": "+",  # Disorder of elbow
        "429554009": "(+)",  # Arthropathy of elbow
        "35185008": "(+)",  # Enthesopathy of elbow region
        "73583000": "(+)",  # Epicondylitis
        "239964003": "(+)",  # Soft tissue lesion of elbow region
        "156659008": "+",  # (Epicondylitis &/or ...
    }

    # Deselect orphaned disorder of elbow
    actions.update_code_statuses(draft=draft, updates=[("128133004", "?")])
    assert dict(draft.code_objs.values_list("code", "status")) == {
        # Part of arthritis search
        "439656005": "+",  # Arthritis of elbow
        "202855006": "(+)",  # Lateral epicondylitis
        "3723001": "-",  # Arthritis
        # Orphans
        "156659008": "+",  # (Epicondylitis &/or ...
    }

    # Delete arthritis search
    actions.delete_search(
        search=draft.searches.get(term="arthritis"),
    )
    assert (
        dict(draft.code_objs.values_list("code", "status"))
        == {
            # Orphans
            "156659008": "+",  # (Epicondylitis &/or ...  kept because included
            "439656005": "+",  # Arthritis of elbow         kept because included
            "202855006": "(+)",  # Lateral epicondylitis    kept because descendant of included
        }
    )

    # Exclude orphaned code - it should disappear
    actions.update_code_statuses(draft=draft, updates=[("156659008", "-")])
    assert (
        dict(draft.code_objs.values_list("code", "status"))
        == {
            # Orphans
            "439656005": "+",  # Arthritis of elbow         kept because included
            "202855006": "(+)",  # Lateral epicondylitis    kept because descendant of included
        }
    )


def test_save(draft_with_no_searches):
    draft = draft_with_no_searches
    actions.save(draft=draft)
    draft.refresh_from_db()

    assert draft.author == draft_with_no_searches.author
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


class FakeLargeCodeList:
    def __len__(self):
        return self.fake_length

    def __init__(self, codes, fake_length):
        self.codes = codes
        self.fake_length = fake_length

    def __iter__(self):
        return iter(self.codes)


def test_create_search_codes_at_limit(version_from_scratch):
    codes = FakeLargeCodeList(codes=[], fake_length=20000)
    result = actions.create_search(draft=version_from_scratch, term="test", codes=codes)
    assert isinstance(result, Search)


def test_create_search_codes_over_limit(version_from_scratch):
    codes = FakeLargeCodeList(codes=[], fake_length=20001)
    result = actions.create_search(
        draft=version_from_scratch, term="term-returning-loads", codes=codes
    )
    assert isinstance(result, dict)
    assert "error" in result
    assert "returned 20,001" in result["message"]
    assert "which exceeds the maximum limit of 20,000" in result["message"]
    assert "term-returning-loads" in result["message"]


@pytest.mark.parametrize(
    "incomplete_code_status", ["?", "!"], ids=["unresolved_code", "conflict_code"]
)
def test_cannot_save_with_incomplete_code_status(
    draft_with_complete_searches, incomplete_code_status
):
    draft = draft_with_complete_searches
    code_obj = draft.code_objs.first()
    code_obj.status = incomplete_code_status
    code_obj.save()

    with pytest.raises(actions.DraftNotReadyError):
        actions.save(draft=draft)

    draft.refresh_from_db()
    assert draft.is_draft
