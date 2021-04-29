import pytest

from ..factories import CodelistFactory, UserFactory, create_published_version
from ..helpers import csv_builder
from .assertions import (
    assert_get_unauthenticated,
    assert_get_unauthorised,
    assert_post_unauthenticated,
    assert_post_unauthorised,
)

pytestmark = pytest.mark.freeze_time("2020-07-23")


def test_get_unauthenticated(client):
    codelist = CodelistFactory()
    assert_get_unauthenticated(client, codelist.get_version_upload_url())


def test_post_unauthenticated(client):
    codelist = CodelistFactory()
    assert_post_unauthenticated(client, codelist.get_version_upload_url())


def test_get_unauthorised(client):
    codelist = CodelistFactory()
    assert_get_unauthorised(client, codelist.get_version_upload_url())


def test_post_unauthorised(client):
    codelist = CodelistFactory()
    assert_post_unauthorised(client, codelist.get_version_upload_url())


def test_get_unauthorised_for_user(client):
    codelist = CodelistFactory(owner=UserFactory())
    assert_get_unauthorised(client, codelist.get_version_upload_url())


def test_post_unauthorised_for_user(client):
    codelist = CodelistFactory(owner=UserFactory())
    assert_post_unauthorised(client, codelist.get_version_upload_url())


def test_get_unknown_codelist(client):
    codelist = CodelistFactory()
    client.force_login(codelist.organisation.users.get())
    url = codelist.get_version_upload_url().replace(codelist.slug, "test")
    response = client.get(url, data={})
    assert response.status_code == 404


def test_post_success(client):
    codelist = create_published_version().codelist
    client.force_login(codelist.organisation.users.get())

    assert codelist.versions.count() == 1

    csv_data = "code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)"
    data = {
        "csv_data": csv_builder(csv_data),
    }

    response = client.post(codelist.get_version_upload_url(), data=data)

    clv = codelist.versions.filter(is_draft=True).get()
    assert response.status_code == 302
    assert response.url == clv.get_absolute_url()
    assert codelist.versions.count() == 2


def test_post_missing_field(client):
    codelist = create_published_version().codelist
    client.force_login(codelist.organisation.users.get())

    response = client.post(codelist.get_version_upload_url(), data={})

    assert response.status_code == 200
    assert "form" in response.context_data
    assert len(response.context_data["form"].errors) == 1
    assert "csv_data" in response.context_data["form"].errors
