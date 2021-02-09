from ..factories import create_draft_version
from .assertions import assert_post_unauthenticated, assert_post_unauthorised


def test_post_unauthenticated(client):
    version = create_draft_version()
    assert_post_unauthenticated(client, version.get_create_url())


def test_post_unauthorised(client):
    version = create_draft_version()
    assert_post_unauthorised(client, version.get_create_url())


def test_post_success(client, new_style_version, organisation_user):
    client.force_login(organisation_user)

    response = client.post(new_style_version.get_create_url())

    draft = new_style_version.codelist.versions.get(draft_owner__isnull=False)
    assert response.status_code == 302
    assert response.url == draft.get_builder_url("draft")
