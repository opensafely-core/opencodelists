from datetime import datetime

from builder.actions import save as save_for_review
from codelists.actions import (
    create_codelist_from_scratch,
    publish_version,
    update_codelist,
)
from opencodelists.actions import add_user_to_organisation
from opencodelists.models import User


def test_get(client, organisation_user):
    user = User.objects.create(
        username="test", name="test", email="test@test.com", password="test"
    )
    client.force_login(user)
    response = client.get("/users/test/")
    assert response.status_code == 200

    # user has no codelists
    for codelist_category in [
        "codelists",
        "authored_for_organisation",
        "under_review",
        "drafts",
    ]:
        assert not response.context[codelist_category]


def test_user_codelists(client, organisation):
    # Create 2 users, both in the same organisation
    user = User.objects.create(
        username="test", name="test", email="test@test.com", password="test"
    )
    other_user = User.objects.create(
        username="test1", name="test1", email="test1@test.com", password="test"
    )
    for org_user in [user, other_user]:
        add_user_to_organisation(
            user=org_user, organisation=organisation, date_joined=datetime.today()
        )
    client.force_login(user)

    # Create a user-owned codelist and an org-owned codelist authored by this user
    # At this stage both are draft
    codelist = create_codelist_from_scratch(
        owner=user, author=user, name="foo1", coding_system_id="snomedct"
    )
    organisation_codelist = create_codelist_from_scratch(
        owner=organisation,
        author=user,
        name="org codelist1",
        coding_system_id="snomedct",
    )

    # codelists owned/authored by another user; these should never appear
    create_codelist_from_scratch(
        owner=other_user, author=other_user, name="foo", coding_system_id="snomedct"
    )
    create_codelist_from_scratch(
        owner=organisation,
        author=other_user,
        name="org codelist",
        coding_system_id="snomedct",
    )

    response = client.get("/users/test/")
    for codelist_category in ["codelists", "authored_for_organisation", "under_review"]:
        assert not response.context[codelist_category]

    assert [cl.id for cl in response.context["drafts"]] == [
        codelist.versions.first().id,
        organisation_codelist.versions.first().id,
    ]

    # make org codelist under-review
    save_for_review(draft=organisation_codelist.versions.first())

    response = client.get("/users/test/")
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
    response = client.get("/users/test/")
    for codelist_category in ["under_review", "drafts"]:
        assert not response.context[codelist_category]
    assert [cl.id for cl in response.context["codelists"]] == [codelist.id]
    assert [cl.id for cl in response.context["authored_for_organisation"]] == [
        organisation_codelist.id
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
    response = client.get("/users/test/")
    # the previously user-owned codelist now appears under "authored_for_organisation"
    for codelist_category in ["codelists", "under_review", "drafts"]:
        assert not response.context[codelist_category]
    assert [cl.id for cl in response.context["authored_for_organisation"]] == [
        codelist.id,
        organisation_codelist.id,
    ]
