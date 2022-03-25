from codelists.actions import publish_version


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


def test_under_review_index(
    client, organisation, version_under_review, old_style_codelist
):
    # The organisation has two codelists whose name matches "style", and both
    # have under review versions

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

    # Get the under-review index.
    rsp = client.get(f"/codelist/{organisation.slug}/under-review/")
    # Assert that only under-review versions are returned
    versions = rsp.context["versions"]
    assert len(versions) == under_review_count + old_style_under_review_count
    for version in versions:
        assert version.status == "under review"


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
    versions = rsp.context["versions"]
    assert len(versions) == under_review_count
    assert version_under_review.id in [version.id for version in versions]
    for version in versions:
        assert version.codelist == version_under_review.codelist
