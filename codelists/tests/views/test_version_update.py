import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404

from codelists.views import version_update
from opencodelists.tests.factories import UserFactory

from ..factories import CodelistFactory, create_draft_version, create_published_version
from ..helpers import csv_builder

pytestmark = pytest.mark.freeze_time("2020-07-23")


def test_versionupdate_unknown_version(rf):
    codelist = CodelistFactory()

    request = rf.get("/")
    request.user = UserFactory()
    with pytest.raises(Http404):
        version_update(
            request,
            organisation_slug=codelist.organisation.slug,
            codelist_slug=codelist.slug,
            qualified_version_str="test",
        )


def test_versionupdate_draft_mismatch(rf):
    version = create_published_version()

    # set the version string to that of a draft
    qualified_version_str = f"{version.qualified_version_str}-draft"

    request = rf.get("/")
    request.user = UserFactory()
    response = version_update(
        request,
        organisation_slug=version.codelist.organisation.slug,
        codelist_slug=version.codelist.slug,
        qualified_version_str=qualified_version_str,
    )

    # we should get redirected to the Version page
    assert response.status_code == 302
    assert response.url == version.get_absolute_url()


def test_versionupdate_form_error(rf):
    version = create_published_version()

    request = rf.post("/", data={})
    request.user = UserFactory()
    response = version_update(
        request,
        organisation_slug=version.codelist.organisation.slug,
        codelist_slug=version.codelist.slug,
        qualified_version_str=version.qualified_version_str,
    )

    assert response.status_code == 200
    assert "form" in response.context_data
    assert "csv_data" in response.context_data["form"].errors


def test_versionupdate_success(rf):
    version = create_draft_version()

    assert version.codelist.versions.count() == 1

    csv_data = "code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)"
    data = {
        "csv_data": csv_builder(csv_data),
    }

    request = rf.post("/", data=data)
    request.user = UserFactory()
    response = version_update(
        request,
        organisation_slug=version.codelist.organisation.slug,
        codelist_slug=version.codelist.slug,
        qualified_version_str=version.qualified_version_str,
    )

    assert response.status_code == 302
    assert (
        response.url
        == f"/codelist/{version.codelist.organisation.slug}/{version.codelist.slug}/2020-07-23-draft/"
    )

    assert version.codelist.versions.count() == 1


def test_versionupdate_not_logged_in(rf):
    version = create_published_version()
    codelist = version.codelist

    assert version.codelist.versions.count() == 1

    request = rf.post("/the/current/url/", data={})
    request.user = AnonymousUser()
    response = version_update(
        request,
        organisation_slug=codelist.organisation.slug,
        codelist_slug=codelist.slug,
        qualified_version_str=version.qualified_version_str,
    )

    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/the/current/url/"
