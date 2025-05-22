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
    for codelist_category in [
        "codelists",
        "authored_for_organisation",
        "under_review",
        "drafts",
    ]:
        assert not response.context[codelist_category]


def test_user_codelists(
    client,
    organisation,
    organisation_user,
    user_without_organisation,
    codelist_from_scratch,
    user_codelist,
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
    for codelist_category in ["codelists", "authored_for_organisation", "under_review"]:
        assert not response.context[codelist_category]

    assert [cl.id for cl in response.context["drafts"]] == [
        organisation_codelist.versions.first().id,
        codelist.versions.first().id,
    ]

    # make org codelist under-review
    save_for_review(draft=organisation_codelist.versions.first())

    response = client.get(user_url)
    assert [cl.id for cl in response.context["drafts"]] == [
        codelist.versions.first().id
    ]
    assert [cl.id for cl in response.context["under_review"]] == [
        organisation_codelist.versions.last().id
    ]

    # publish both codelists
    save_for_review(draft=codelist.versions.first())
    publish_version(version=codelist.versions.last())
    publish_version(version=organisation_codelist.versions.last())
    user_codelist_version_id = codelist.latest_published_version().id
    org_codelist_version_id = organisation_codelist.latest_published_version().id
    response = client.get(user_url)
    for codelist_category in ["under_review", "drafts"]:
        assert not response.context[codelist_category]
    assert [cl.id for cl in response.context["codelists"]] == [user_codelist_version_id]
    assert [cl.id for cl in response.context["authored_for_organisation"]] == [
        org_codelist_version_id
    ]

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
    for codelist_category in ["codelists", "under_review", "drafts"]:
        assert not response.context[codelist_category]
    assert [cl.id for cl in response.context["authored_for_organisation"]] == [
        org_codelist_version_id,
        user_codelist_version_id,
    ]
