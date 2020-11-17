import pytest
from django.urls import reverse

from ..factories import CodelistFactory, create_draft_version, create_published_version
from ..helpers import csv_builder
from .assertions import (
    assert_get_unauthenticated,
    assert_get_unauthorised,
    assert_post_unauthenticated,
    assert_post_unauthorised,
)

pytestmark = pytest.mark.freeze_time("2020-07-23")


def test_get_unauthenticated(client):
    version = create_draft_version()
    assert_get_unauthenticated(client, version.get_update_url())


def test_post_unauthenticated(client):
    version = create_draft_version()
    assert_post_unauthenticated(client, version.get_update_url())


def test_get_unauthorised(client):
    version = create_draft_version()
    assert_get_unauthorised(client, version.get_update_url())


def test_post_unauthorised(client):
    version = create_draft_version()
    assert_post_unauthorised(client, version.get_update_url())


def test_get_unknown_version(client):
    codelist = CodelistFactory()
    client.force_login(codelist.organisation.regular_user)

    kwargs = dict(
        organisation_slug=codelist.organisation.slug,
        codelist_slug=codelist.slug,
        qualified_version_str="test",
    )
    url = reverse("codelists:version_update", kwargs=kwargs)

    response = client.get(url)

    assert response.status_code == 404


def test_get_published_with_draft_url(client):
    version = create_published_version()
    client.force_login(version.codelist.organisation.regular_user)

    kwargs = dict(
        organisation_slug=version.codelist.organisation.slug,
        codelist_slug=version.codelist.slug,
        qualified_version_str=f"{version.qualified_version_str}-draft",
    )
    url = reverse("codelists:version_update", kwargs=kwargs)

    response = client.post(url)

    # we should get redirected to the Version page
    assert response.status_code == 302
    assert response.url == version.get_absolute_url()


def test_post_success(client):
    version = create_draft_version()
    client.force_login(version.codelist.organisation.regular_user)

    assert version.codelist.versions.count() == 1

    csv_data = "code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)"
    data = {
        "csv_data": csv_builder(csv_data),
    }

    response = client.post(version.get_update_url(), data=data)

    assert response.status_code == 302
    assert (
        response.url
        == f"/codelist/{version.codelist.organisation.slug}/{version.codelist.slug}/2020-07-23-draft/"
    )

    assert version.codelist.versions.count() == 1


def test_post_form_error(client):
    version = create_published_version()
    client.force_login(version.codelist.organisation.regular_user)

    response = client.post(version.get_update_url())

    assert response.status_code == 200
    assert "form" in response.context_data
    assert "csv_data" in response.context_data["form"].errors
