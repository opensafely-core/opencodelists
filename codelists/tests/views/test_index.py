import pytest

from codelists.actions import publish_version
from codelists.models import Handle, Status
from codelists.views.index import _parse_search_query
from opencodelists.list_utils import flatten


def test_search_only_returns_codelists_with_published_versions(
    client, organisation, old_style_codelist, new_style_codelist
):
    # The organisation has two codelists whose name matches "style" ("New-style
    # codelist" and "Old-style codelist").  However, "Old-style codelist" does not have
    # any published versions, and so should not appear in search results.

    # Validate our assumptions about the fixtures.
    assert old_style_codelist.organisation == organisation
    assert old_style_codelist.versions.filter(status="published").count() == 0
    assert new_style_codelist.organisation == organisation
    assert new_style_codelist.versions.filter(status="published").count() > 0

    # Do a search.
    rsp = client.get(f"/codelist/{organisation.slug}/?q=style")

    # Assert that only one codelist is returned.
    assert len(rsp.context["codelists_page"].object_list) == 1
    codelist = rsp.context["codelists_page"].object_list[0]
    assert codelist.slug == "new-style-codelist"


def test_paginate_codelists(client, organisation, create_codelists):
    # Create enough published codelists to paginate (codelist index page is paginated by 15)
    create_codelists(30, owner=organisation, status=Status.PUBLISHED)
    published_for_organisation = [
        handle.codelist
        for handle in Handle.objects.filter(is_current=True, organisation=organisation)
        if handle.codelist.has_published_versions()
    ]
    assert len(published_for_organisation) > 30

    rsp = client.get(f"/codelist/{organisation.slug}/")
    codelist_page_obj = rsp.context["codelists_page"]
    assert len(codelist_page_obj.object_list) == 15
    assert codelist_page_obj.number == 1

    rsp = client.get(f"/codelist/{organisation.slug}/?page=3")
    codelist_page_obj = rsp.context["codelists_page"]
    assert len(codelist_page_obj.object_list) == len(published_for_organisation) - 30


def test_under_review_index(
    client,
    organisation,
    version_under_review,
    old_style_codelist,
    dmd_codelist,
    null_codelist,
):
    # The organisation has three codelists (new style, old style, dmd)
    # All three codelists have under review versions

    # Validate our assumptions about the fixtures.
    assert version_under_review.codelist.organisation == organisation
    assert version_under_review.status == "under review"
    under_review_count = version_under_review.codelist.versions.filter(
        status="under review"
    ).count()
    assert under_review_count > 0

    assert old_style_codelist.organisation == organisation
    old_style_under_review_count = old_style_codelist.versions.filter(
        status="under review"
    ).count()
    assert old_style_under_review_count > 0

    assert dmd_codelist.organisation == organisation
    dmd_under_review_count = dmd_codelist.versions.filter(status="under review").count()
    assert dmd_under_review_count > 0

    assert null_codelist.organisation == organisation
    null_under_review_count = null_codelist.versions.filter(
        status="under review"
    ).count()
    assert null_under_review_count > 0

    # Get the under-review index.
    rsp = client.get(f"/codelist/{organisation.slug}/under-review/")
    # Assert that only under-review versions are returned
    versions = rsp.context["versions_page"].object_list
    assert (
        len(versions)
        == under_review_count
        + old_style_under_review_count
        + dmd_under_review_count
        + null_under_review_count
    )
    for version in versions:
        assert version.status == "under review"


def test_paginate_under_review_versions(client, organisation, create_codelists):
    # Create enough published codelists to paginate (under-review index page is paginated by 30)
    create_codelists(40, status=Status.UNDER_REVIEW, owner=organisation)
    under_review_for_organisation = flatten(
        [
            list(handle.codelist.versions.filter(status=Status.UNDER_REVIEW))
            for handle in Handle.objects.filter(
                is_current=True, organisation=organisation
            )
        ]
    )
    assert len(under_review_for_organisation) > 40

    rsp = client.get(f"/codelist/{organisation.slug}/under-review/")
    codelist_page_obj = rsp.context["versions_page"]
    assert len(codelist_page_obj.object_list) == 30
    assert codelist_page_obj.number == 1

    rsp = client.get(f"/codelist/{organisation.slug}/under-review/?page=2")
    codelist_page_obj = rsp.context["versions_page"]
    assert len(codelist_page_obj.object_list) == len(under_review_for_organisation) - 30


def test_search_only_returns_codelists_with_under_review_versions(
    client, organisation, version_under_review, old_style_codelist
):
    # The organisation has two codelists whose name matches "style" ("New-style
    # codelist" and "Old-style codelist").  However, only "New-style codelist" has
    # under review versions, and so only these should appear in search results.

    # Validate our assumptions about the fixtures.
    assert version_under_review.codelist.organisation == organisation
    assert version_under_review.status == "under review"
    under_review_count = version_under_review.codelist.versions.filter(
        status="under review"
    ).count()
    assert under_review_count > 0

    # publish the old-style-codelist
    old_style_under_review_version = old_style_codelist.versions.filter(
        status="under review"
    ).first()
    publish_version(version=old_style_under_review_version)
    assert old_style_codelist.organisation == organisation
    assert old_style_codelist.versions.filter(status="under review").count() == 0

    # Do a search.
    rsp = client.get(f"/codelist/{organisation.slug}/under-review/?q=style")
    # Assert that only versions related to one codelist are returned
    versions = rsp.context["versions_page"].object_list
    assert len(versions) == under_review_count
    assert version_under_review.id in [version.id for version in versions]
    for version in versions:
        assert version.codelist == version_under_review.codelist


@pytest.mark.parametrize(
    "query,expected_quoted_phrases,expected_individual_words",
    [
        # Basic functionality
        ("oneword", [], ["oneword"]),
        ("two words", [], ["two", "words"]),
        ('"quoted words"', ["quoted words"], []),
        ('word "and quoted" words', ["and quoted"], ["word", "words"]),
        ('"two quoted" "phrases"', ["two quoted", "phrases"], []),
        (
            '"two quoted" "phrases" and other words',
            ["two quoted", "phrases"],
            ["and", "other", "words"],
        ),
        # Edge cases
        ("", [], []),
        ("   ", [], []),
        ('empty "" quotes', [""], ["empty", "quotes"]),
        ('lone "quote', [], ["lone", '"quote']),
        # Other scenarios
        (
            '  lots   "of word"   padding  ',
            ["of word"],
            ["lots", "padding"],
        ),
        ('"adjacent""quotes"', ["adjacent", "quotes"], []),
        (
            '"three"quotes"',
            ["three"],
            ['quotes"'],
        ),
    ],
)
def test_parse_search_query(query, expected_quoted_phrases, expected_individual_words):
    """Test parsing various search query formats."""
    quoted_phrases, individual_words = _parse_search_query(query)
    assert quoted_phrases == expected_quoted_phrases
    assert individual_words == expected_individual_words
