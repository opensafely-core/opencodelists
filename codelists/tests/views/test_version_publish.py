from django.urls import reverse

from ..factories import CodelistFactory, create_draft_version
from .assertions import assert_post_unauthenticated, assert_post_unauthorised


def test_post_unauthenticated(client):
    version = create_draft_version()
    assert_post_unauthenticated(client, version.get_publish_url())


def test_post_unauthorised(client):
    version = create_draft_version()
    assert_post_unauthorised(client, version.get_publish_url())


def test_post_success(client):
    version = create_draft_version()
    client.force_login(version.codelist.organisation.users.get())

    response = client.post(version.get_publish_url())
    version.refresh_from_db()

    assert response.status_code == 302
    assert response.url == version.get_absolute_url()
    assert not version.is_draft


def test_post_unknown_version(client):
    codelist = CodelistFactory()
    client.force_login(codelist.organisation.users.get())

    kwargs = dict(
        organisation_slug=codelist.organisation.slug,
        codelist_slug=codelist.slug,
        tag_or_hash="test",
    )
    url = reverse("codelists:organisation_version_publish", kwargs=kwargs)

    response = client.post(url)

    assert response.status_code == 404
