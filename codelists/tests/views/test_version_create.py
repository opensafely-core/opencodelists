from codelists import actions

from ..factories import create_draft_version
from .assertions import assert_post_unauthenticated, assert_post_unauthorised


def test_post_unauthenticated(client):
    version = create_draft_version()
    assert_post_unauthenticated(client, version.get_create_url())


def test_post_unauthorised(client):
    version = create_draft_version()
    assert_post_unauthorised(client, version.get_create_url())


def test_post_success(client):
    version = create_draft_version()
    codelist = version.codelist
    client.force_login(codelist.organisation.regular_user)
    converted_version = actions.convert_codelist_to_new_style(codelist=codelist)

    response = client.post(converted_version.get_create_url())

    draft = codelist.versions.get(draft_owner__isnull=False)
    assert response.status_code == 302
    assert response.url == draft.get_builder_url("draft")
