from codelists.coding_systems import most_recent_database_alias

from ...models import Status
from .assertions import assert_post_unauthenticated, assert_post_unauthorised
from .helpers import force_login


def test_post_unauthenticated(client, version):
    assert_post_unauthenticated(client, version.get_create_url())


def test_post_unauthorised(client, version):
    assert_post_unauthorised(client, version.get_create_url())


def test_post_success(client, version):
    force_login(version, client)

    assert (
        version.codelist.versions.filter(
            author__isnull=False, status=Status.DRAFT
        ).exists()
        is False
    )
    response = client.post(
        version.get_create_url(),
        {"coding_system_database_alias": most_recent_database_alias("snomedct")},
    )

    draft = version.codelist.versions.get(author__isnull=False, status=Status.DRAFT)
    assert response.status_code == 302
    assert response.url == draft.get_builder_draft_url()


def test_post_success_no_coding_system_database_alias(client, version):
    force_login(version, client)

    assert (
        version.codelist.versions.filter(
            author__isnull=False, status=Status.DRAFT
        ).exists()
        is False
    )
    client.post(
        version.get_create_url(),
        {"coding_system_database_alias": ""},
    )

    draft = version.codelist.versions.get(author__isnull=False, status=Status.DRAFT)
    # defaults to most recent database alias for the version's coding system release
    assert draft.coding_system.database_alias == most_recent_database_alias("snomedct")
