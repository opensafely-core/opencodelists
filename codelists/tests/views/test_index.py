import pytest

from codelists.models import Handle, Status
from codelists.views.index import _parse_search_query


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


def test_search_ranking(client, organisation, create_codelist):
    """Tests that:
    - words can appear in any order
    - highest rank is exact match in name
    - second is all words in name
    - third is any word in name
    - last is all words in description"""
    codelist1 = create_codelist(name="Codelist 1", description="Type 2 diabetes")
    codelist2 = create_codelist(name="Diabetes", description="type 2")
    codelist3 = create_codelist(name="Diabetes type 2")
    codelist4 = create_codelist(name="Type 2 diabetes")

    rsp = client.get(f"/codelist/{organisation.slug}/?q=type+2+diabetes")
    codelists_from_search = rsp.context["codelists_page"].object_list

    assert len(codelists_from_search) == 4
    assert codelists_from_search[0].slug == codelist4.slug
    assert codelists_from_search[1].slug == codelist3.slug
    assert codelists_from_search[2].slug == codelist2.slug
    assert codelists_from_search[3].slug == codelist1.slug
