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
    assert len(rsp.context["codelists"]) == 1
    codelist = rsp.context["codelists"][0]
    assert codelist.slug == "new-style-codelist"
