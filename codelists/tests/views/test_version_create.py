import pytest
from django.http import Http404

from codelists.views import version_create

from ..factories import CodelistFactory, create_published_version
from ..helpers import csv_builder
from .assertions import (
    assert_get_unauthenticated,
    assert_get_unauthorised,
    assert_post_unauthenticated,
    assert_post_unauthorised,
)

pytestmark = pytest.mark.freeze_time("2020-07-23")


def test_get_unauthenticated(rf):
    codelist = CodelistFactory()
    assert_get_unauthenticated(rf, version_create, codelist)


def test_post_unauthenticated(rf):
    codelist = CodelistFactory()
    assert_post_unauthenticated(rf, version_create, codelist)


def test_get_unauthorised(rf):
    codelist = CodelistFactory()
    assert_get_unauthorised(rf, version_create, codelist)


def test_post_unauthorised(rf):
    codelist = CodelistFactory()
    assert_post_unauthorised(rf, version_create, codelist)


def test_get_unknown_codelist(rf):
    codelist = CodelistFactory()

    request = rf.get("/")
    request.user = codelist.organisation.regular_user

    with pytest.raises(Http404):
        version_create(
            request, organisation_slug=codelist.organisation.slug, codelist_slug="test"
        )


def test_post_success(rf):
    codelist = create_published_version().codelist

    assert codelist.versions.count() == 1

    csv_data = "code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)"
    data = {
        "csv_data": csv_builder(csv_data),
    }

    request = rf.post("/", data=data)
    request.user = codelist.organisation.regular_user
    response = version_create(
        request,
        organisation_slug=codelist.organisation.slug,
        codelist_slug=codelist.slug,
    )

    assert response.status_code == 302
    assert (
        response.url
        == f"/codelist/{codelist.organisation.slug}/{codelist.slug}/2020-07-23-a-draft/"
    )

    assert codelist.versions.count() == 2


def test_post_missing_field(rf):
    codelist = create_published_version().codelist

    request = rf.post("/", data={})
    request.user = codelist.organisation.regular_user
    response = version_create(
        request,
        organisation_slug=codelist.organisation.slug,
        codelist_slug=codelist.slug,
    )

    assert response.status_code == 200
    assert "form" in response.context_data
    assert len(response.context_data["form"].errors) == 1
    assert "csv_data" in response.context_data["form"].errors
