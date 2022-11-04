from codelists.coding_systems import CODING_SYSTEMS

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
    coding_system_database_alias = (
        CODING_SYSTEMS["snomedct"].most_recent().database_alias
    )
    response = client.post(
        version.get_create_url(),
        {"coding_system_database_alias": coding_system_database_alias},
    )

    draft = version.codelist.versions.get(author__isnull=False, status=Status.DRAFT)
    assert response.status_code == 302
    assert response.url == draft.get_builder_draft_url()
