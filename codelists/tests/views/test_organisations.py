from datetime import datetime

import pytest
from django.utils import timezone

from codelists.actions import publish_version
from codelists.models import Codelist, CodelistVersion, Handle, Status
from opencodelists.list_utils import flatten


def aware_datetime(year: int, month: int, day: int) -> datetime:
    """Return a timezone-aware datetime for deterministic timestamp assertions."""

    return timezone.make_aware(datetime(year, month, day))


def test_published_index_only_returns_public_codelists_with_published_versions(
    client, organisation, old_style_codelist, new_style_codelist, create_codelist
):
    # The organisation has two codelists whose name matches "style".  However,
    # "Old-style codelist" does not have any published versions, and so should not
    # appear in the published organisation results.
    private_codelist = create_codelist(name="Private style codelist")
    private_codelist.is_private = True
    private_codelist.save()

    assert old_style_codelist.organisation == organisation
    assert old_style_codelist.versions.filter(status=Status.PUBLISHED).count() == 0
    assert new_style_codelist.organisation == organisation
    assert new_style_codelist.versions.filter(status=Status.PUBLISHED).count() > 0
    assert private_codelist.organisation == organisation
    assert private_codelist.versions.filter(status=Status.PUBLISHED).count() > 0

    rsp = client.get(f"/codelist/{organisation.slug}/?q=style")

    assert rsp.status_code == 200
    assert "codelists/organisation_published.html" in [
        template.name for template in rsp.templates
    ]
    assert rsp.context["organisation"] == organisation
    assert rsp.context["q"] == "style"
    codelists = list(rsp.context["page_obj"].object_list)
    assert codelists == [new_style_codelist]


def test_paginate_published_codelists(client, organisation, create_codelists):
    create_codelists(70, owner=organisation, status=Status.PUBLISHED)
    published_for_organisation = [
        handle.codelist
        for handle in Handle.objects.filter(is_current=True, organisation=organisation)
        if handle.codelist.has_published_versions()
    ]
    assert len(published_for_organisation) > 70

    rsp = client.get(f"/codelist/{organisation.slug}/")
    page_obj = rsp.context["page_obj"]
    assert len(page_obj.object_list) == 50
    assert page_obj.number == 1

    rsp = client.get(f"/codelist/{organisation.slug}/?page=2")
    page_obj = rsp.context["page_obj"]
    assert len(page_obj.object_list) == min(50, len(published_for_organisation) - 50)


@pytest.mark.parametrize(
    ("path", "status"),
    [
        ("", Status.PUBLISHED),
        ("under-review/", Status.UNDER_REVIEW),
    ],
)
def test_organisation_pagination_preserves_search_and_sort_query(
    client, organisation, create_codelists, path, status
):
    create_codelists(70, owner=organisation, status=status)

    rsp = client.get(
        f"/codelist/{organisation.slug}/{path}",
        {"q": "Codelist", "sort": "name", "direction": "desc"},
    )

    assert rsp.context["pagination"]["next_url"] == (
        "?page=2&q=Codelist&sort=name&direction=desc"
    )
    assert 'href="?page=2&amp;q=Codelist&amp;sort=name&amp;direction=desc"' in (
        rsp.content.decode()
    )


@pytest.mark.parametrize(
    ("sort", "direction", "expected_names"),
    [
        (
            "name",
            "asc",
            ["SNOMED alpha", "SNOMED Bravo", "SNOMED Charlie"],
        ),
        (
            "name",
            "desc",
            ["SNOMED Charlie", "SNOMED Bravo", "SNOMED alpha"],
        ),
        (
            "updated_at",
            "asc",
            ["SNOMED Charlie", "SNOMED alpha", "SNOMED Bravo"],
        ),
        (
            "updated_at",
            "desc",
            ["SNOMED Bravo", "SNOMED alpha", "SNOMED Charlie"],
        ),
    ],
)
def test_published_codelists_search_and_sort(
    client, organisation, create_codelist, sort, direction, expected_names
):
    bravo = create_codelist("SNOMED Bravo")
    alpha = create_codelist("SNOMED alpha")
    charlie = create_codelist("SNOMED Charlie")
    create_codelist("Ignored published")

    Codelist.objects.filter(pk=bravo.pk).update(updated_at=aware_datetime(2020, 3, 1))
    Codelist.objects.filter(pk=alpha.pk).update(updated_at=aware_datetime(2020, 2, 1))
    Codelist.objects.filter(pk=charlie.pk).update(updated_at=aware_datetime(2020, 1, 1))

    rsp = client.get(
        f"/codelist/{organisation.slug}/",
        {"q": "SNOMED", "sort": sort, "direction": direction},
    )

    assert [
        codelist.name for codelist in rsp.context["page_obj"].object_list
    ] == expected_names


def test_published_index_does_not_duplicate_codelists_with_multiple_published_versions(
    client, organisation, null_codelist
):
    null_codelist.versions.update(status=Status.PUBLISHED)
    assert null_codelist.versions.filter(status=Status.PUBLISHED).count() > 1

    rsp = client.get(f"/codelist/{organisation.slug}/")

    codelists = list(rsp.context["page_obj"].object_list)
    assert codelists.count(null_codelist) == 1


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
    assert "codelists/organisation_review.html" in [
        template.name for template in rsp.templates
    ]
    assert rsp.context["organisation"] == organisation
    # Assert that only under-review versions are returned
    versions = rsp.context["page_obj"].object_list
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
    # Create enough published codelists to paginate.
    create_codelists(70, status=Status.UNDER_REVIEW, owner=organisation)
    under_review_for_organisation = flatten(
        [
            list(handle.codelist.versions.filter(status=Status.UNDER_REVIEW))
            for handle in Handle.objects.filter(
                is_current=True, organisation=organisation
            )
        ]
    )
    assert len(under_review_for_organisation) > 70

    rsp = client.get(f"/codelist/{organisation.slug}/under-review/")
    page_obj = rsp.context["page_obj"]
    assert len(page_obj.object_list) == 50
    assert page_obj.number == 1

    rsp = client.get(f"/codelist/{organisation.slug}/under-review/?page=2")
    page_obj = rsp.context["page_obj"]
    assert len(page_obj.object_list) == min(50, len(under_review_for_organisation) - 50)


@pytest.mark.parametrize(
    ("sort", "direction", "expected_names"),
    [
        (
            "name",
            "asc",
            ["DM+D alpha", "DM+D Bravo", "DM+D Charlie"],
        ),
        (
            "name",
            "desc",
            ["DM+D Charlie", "DM+D Bravo", "DM+D alpha"],
        ),
        (
            "created_at",
            "asc",
            ["DM+D Charlie", "DM+D alpha", "DM+D Bravo"],
        ),
        (
            "created_at",
            "desc",
            ["DM+D Bravo", "DM+D alpha", "DM+D Charlie"],
        ),
    ],
)
def test_under_review_versions_search_and_sort(
    client, organisation, create_codelist, sort, direction, expected_names
):
    bravo = create_codelist("DM+D Bravo", status=Status.UNDER_REVIEW)
    alpha = create_codelist("DM+D alpha", status=Status.UNDER_REVIEW)
    charlie = create_codelist("DM+D Charlie", status=Status.UNDER_REVIEW)
    create_codelist("Ignored review", status=Status.UNDER_REVIEW)

    CodelistVersion.objects.filter(codelist=bravo).update(
        created_at=aware_datetime(2020, 3, 1)
    )
    CodelistVersion.objects.filter(codelist=alpha).update(
        created_at=aware_datetime(2020, 2, 1)
    )
    CodelistVersion.objects.filter(codelist=charlie).update(
        created_at=aware_datetime(2020, 1, 1)
    )

    rsp = client.get(
        f"/codelist/{organisation.slug}/under-review/",
        {"q": "DM+D", "sort": sort, "direction": direction},
    )

    assert (
        [version.codelist.name for version in rsp.context["page_obj"].object_list]
    ) == expected_names


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
    versions = rsp.context["page_obj"].object_list
    assert len(versions) == under_review_count
    assert version_under_review.id in [version.id for version in versions]
    for version in versions:
        assert version.codelist == version_under_review.codelist
