from datetime import datetime

from django.urls import reverse

from builder.actions import save as save_for_review
from codelists.actions import publish_version, update_codelist
from opencodelists.actions import add_user_to_organisation


def test_get(client, user_without_organisation):
    client.force_login(user_without_organisation)
    response = client.get(reverse("user", args=(user_without_organisation.username,)))
    assert response.status_code == 200

    # user_without_organisation has no codelists
    for codelist_category in ["published_codelists", "all_codelists"]:
        assert not response.context[codelist_category]


def test_user_codelists(
    client,
    organisation,
    organisation_user,
    user_without_organisation,
    codelist_from_scratch,
    user_codelist_from_scratch,
):
    test_user = user_without_organisation
    # Add test_user to same organisation as organisation_user

    add_user_to_organisation(
        user=test_user, organisation=organisation, date_joined=datetime.today()
    )
    client.force_login(test_user)

    user_url = reverse("user", args=(test_user.username,))

    # Ensure we have a user-owned codelist and an org-owned codelist authored by this user
    # Both of these are currently in draft
    organisation_codelist = codelist_from_scratch
    org_cl_version = organisation_codelist.versions.first()
    org_cl_version.author = test_user
    org_cl_version.save()

    codelist = user_codelist_from_scratch
    cl_handle = codelist.handles.first()
    cl_handle.user = test_user
    cl_handle.organisation = None
    cl_handle.save()
    cl_version = codelist.versions.first()
    cl_version.author = test_user
    cl_version.save()

    # organisation_user also has codelists; these should never appear for our test user
    assert organisation_user.codelists.count() >= 1

    response = client.get(user_url)
    assert not response.context["published_codelists"]
    assert not [
        version
        for codelist in response.context["all_codelists"]
        for version in codelist["versions"]
        if version.is_under_review
    ]

    assert [
        version.id
        for codelist in response.context["all_codelists"]
        for version in codelist["versions"]
        if version.is_draft
    ] == [
        organisation_codelist.versions.first().id,
        codelist.versions.first().id,
    ]

    # make org codelist under-review
    save_for_review(draft=organisation_codelist.versions.first())

    response = client.get(user_url)
    assert [
        version.id
        for codelist in response.context["all_codelists"]
        for version in codelist["versions"]
        if version.is_draft
    ] == [codelist.versions.first().id]
    assert [
        version.id
        for codelist in response.context["all_codelists"]
        for version in codelist["versions"]
        if version.is_under_review
    ] == [organisation_codelist.versions.last().id]

    # publish both codelists
    save_for_review(draft=codelist.versions.first())
    publish_version(version=codelist.versions.last())
    publish_version(version=organisation_codelist.versions.last())
    user_codelist_version_id = codelist.latest_published_version().id
    org_codelist_version_id = organisation_codelist.latest_published_version().id
    response = client.get(user_url)
    assert not [
        version
        for codelist in response.context["all_codelists"]
        for version in codelist["versions"]
        if version.is_under_review or version.is_draft
    ]
    assert [
        version.id
        for cl in response.context["all_codelists"]
        for version in cl["versions"]
        if not version.organisation
    ] == [user_codelist_version_id]
    assert [
        version.id
        for cl in response.context["all_codelists"]
        for version in cl["versions"]
        if version.organisation
    ] == [org_codelist_version_id]

    # change the owner for the user-owned codelist to an organisation
    update_codelist(
        codelist=codelist,
        owner=organisation,
        name=codelist.name,
        slug=codelist.slug,
        description=codelist.description,
        methodology=codelist.methodology,
        references={},
        signoffs={},
    )
    response = client.get(user_url)
    # the previously user-owned codelist now appears under "authored_for_organisation"
    assert not [
        version.id
        for cl in response.context["all_codelists"]
        for version in cl["versions"]
        if not version.organisation
    ]
    assert [
        version.id
        for cl in response.context["all_codelists"]
        for version in cl["versions"]
        if version.organisation
    ] == [
        org_codelist_version_id,
        user_codelist_version_id,
    ]


def test_user_codelists_sort_user_first(
    client,
    user,
    organisation,
    codelist_from_scratch,
    user_codelist_from_scratch,
):
    # Give both codelists the same name (case-insensitive), one user-owned and one org-owned
    update_codelist(
        codelist=user_codelist_from_scratch,
        owner=user,
        name="alpha list",
        slug="alpha-list-user",
        description=user_codelist_from_scratch.description,
        methodology=user_codelist_from_scratch.methodology,
        references={},
        signoffs={},
    )
    update_codelist(
        codelist=codelist_from_scratch,
        owner=organisation,
        name="ALPHA LIST",
        slug="alpha-list-org",
        description=codelist_from_scratch.description,
        methodology=codelist_from_scratch.methodology,
        references={},
        signoffs={},
    )

    client.force_login(user)
    response = client.get(reverse("user", args=(user.username,)))

    matching_codelists = [
        codelist["codelist"]
        for codelist in response.context["all_codelists"]
        if codelist["codelist"].name.casefold() == "alpha list"
    ]
    assert [codelist.owner for codelist in matching_codelists] == [user, organisation]


def test_published_codelists_sorted_same_as_all_codelists(
    client,
    user,
    user_codelist,
    user_codelist_from_scratch,
):
    update_codelist(
        codelist=user_codelist,
        owner=user,
        name="zeta list",
        slug="zeta-list",
        description=user_codelist.description,
        methodology=user_codelist.methodology,
        references={},
        signoffs={},
    )
    update_codelist(
        codelist=user_codelist_from_scratch,
        owner=user,
        name="ALPHA LIST",
        slug="alpha-list",
        description=user_codelist_from_scratch.description,
        methodology=user_codelist_from_scratch.methodology,
        references={},
        signoffs={},
    )
    save_for_review(draft=user_codelist_from_scratch.versions.first())
    publish_version(version=user_codelist_from_scratch.versions.last())

    client.force_login(user)
    response = client.get(reverse("user", args=(user.username,)))

    codelist_ids = {user_codelist.id, user_codelist_from_scratch.id}
    all_codelist_ids = [
        codelist["codelist"].id
        for codelist in response.context["all_codelists"]
        if codelist["codelist"].id in codelist_ids
    ]
    published_codelist_ids = [
        version.codelist.id
        for version in response.context["published_codelists"]
        if version.codelist.id in codelist_ids
    ]
    assert published_codelist_ids == all_codelist_ids
