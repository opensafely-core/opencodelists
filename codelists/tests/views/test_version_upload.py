from opencodelists.tests.assertions import assert_difference, assert_no_difference

from ..helpers import csv_builder
from .assertions import (
    assert_get_unauthenticated,
    assert_get_unauthorised,
    assert_post_unauthenticated,
    assert_post_unauthorised,
)
from .helpers import force_login


def test_get_unauthenticated(client, old_style_codelist):
    assert_get_unauthenticated(client, old_style_codelist.get_version_upload_url())


def test_post_unauthenticated(client, old_style_codelist):
    assert_post_unauthenticated(client, old_style_codelist.get_version_upload_url())


def test_get_unauthorised(client, old_style_codelist):
    assert_get_unauthorised(client, old_style_codelist.get_version_upload_url())


def test_post_unauthorised(client, old_style_codelist):
    assert_post_unauthorised(client, old_style_codelist.get_version_upload_url())


def test_get_unknown_codelist(client, old_style_codelist):
    force_login(old_style_codelist, client)
    url = old_style_codelist.get_version_upload_url().replace(
        old_style_codelist.slug, "test"
    )
    response = client.get(url, data={})
    assert response.status_code == 404


def test_post_success(client, old_style_codelist):
    force_login(old_style_codelist, client)

    csv_data = "code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)"
    data = {
        "csv_data": csv_builder(csv_data),
    }

    with assert_difference(old_style_codelist.versions.count, expected_difference=1):
        response = client.post(old_style_codelist.get_version_upload_url(), data=data)

    clv = old_style_codelist.versions.filter().last()
    assert response.status_code == 302
    assert response.url == clv.get_absolute_url()


def test_post_missing_field(client, old_style_codelist):
    force_login(old_style_codelist, client)

    with assert_no_difference(old_style_codelist.versions.count):
        response = client.post(old_style_codelist.get_version_upload_url(), data={})

    assert response.status_code == 200
    assert "form" in response.context_data
    assert len(response.context_data["form"].errors) == 1
    assert "csv_data" in response.context_data["form"].errors
