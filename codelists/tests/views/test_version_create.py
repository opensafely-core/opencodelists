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
            draft_owner__isnull=False, status=Status.DRAFT
        ).exists()
        is False
    )

    response = client.post(version.get_create_url())

    draft = version.codelist.versions.get(
        draft_owner__isnull=False, status=Status.DRAFT
    )
    assert response.status_code == 302
    assert response.url == draft.get_builder_draft_url()
