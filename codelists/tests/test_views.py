import csv
from io import StringIO

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from pytest_django.asserts import assertContains, assertRedirects

from codelists.views import (
    CreateCodelist,
    VersionCreate,
    VersionUpdate,
    version_publish,
)
from opencodelists.tests.factories import ProjectFactory, UserFactory

from . import factories
from .helpers import csv_builder

pytestmark = [
    pytest.mark.freeze_time("2020-07-23"),
    pytest.mark.filterwarnings(
        "ignore::DeprecationWarning:bleach",
        "ignore::django.utils.deprecation.RemovedInDjango40Warning:debug_toolbar",
    ),
]


@pytest.fixture()
def logged_in_client(client, django_user_model):
    """A Django test client logged in a user."""
    client.force_login(UserFactory())
    return client


def test_createcodelist_success(rf):
    project = ProjectFactory()
    signoff_user = UserFactory()

    assert project.codelists.count() == 0

    csv_data = "code,description\n1067731000000107,Injury whilst swimming (disorder)"
    data = {
        "name": "Test Codelist",
        "coding_system_id": "snomedct",
        "description": "This is a test",
        "methodology": "This is how we did it",
        "csv_data": csv_builder(csv_data),
        "reference-TOTAL_FORMS": "1",
        "reference-INITIAL_FORMS": "0",
        "reference-MIN_NUM_FORMS": "0",
        "reference-MAX_NUM_FORMS": "1000",
        "reference-0-text": "foo",
        "reference-0-url": "http://example.com",
        "signoff-TOTAL_FORMS": "1",
        "signoff-INITIAL_FORMS": "0",
        "signoff-MIN_NUM_FORMS": "0",
        "signoff-MAX_NUM_FORMS": "1000",
        "signoff-0-user": signoff_user.username,
        "signoff-0-date": "2020-01-23",
    }

    request = rf.post("/", data=data)
    request.user = UserFactory()
    response = CreateCodelist.as_view()(request, project_slug=project.slug)

    assert response.status_code == 302
    assert response.url == f"/codelist/{project.slug}/test-codelist/"

    assert project.codelists.count() == 1
    codelist = project.codelists.first()
    assert codelist.name == "Test Codelist"

    # we should have one reference to example.com
    assert codelist.references.count() == 1
    ref = codelist.references.first()
    assert ref.url == "http://example.com"

    # we should have one signoff by signoff user
    assert codelist.signoffs.count() == 1
    signoff = codelist.signoffs.first()
    assert signoff.user == signoff_user


def test_createcodelist_invalid_post(rf):
    project = ProjectFactory()
    signoff_user = UserFactory()

    assert project.codelists.count() == 0

    csv_data = "code,description\n1067731000000107,Injury whilst swimming (disorder)"

    # missing signoff-0-date
    data = {
        "name": "Test Codelist",
        "coding_system_id": "snomedct",
        "description": "This is a test",
        "methodology": "This is how we did it",
        "csv_data": csv_builder(csv_data),
        "reference-TOTAL_FORMS": "1",
        "reference-INITIAL_FORMS": "0",
        "reference-MIN_NUM_FORMS": "0",
        "reference-MAX_NUM_FORMS": "1000",
        "reference-0-text": "foo",
        "reference-0-url": "http://example.com",
        "signoff-TOTAL_FORMS": "1",
        "signoff-INITIAL_FORMS": "0",
        "signoff-MIN_NUM_FORMS": "0",
        "signoff-MAX_NUM_FORMS": "1000",
        "signoff-0-user": signoff_user.username,
    }

    request = rf.post("/", data=data)
    request.user = UserFactory()
    response = CreateCodelist.as_view()(request, project_slug=project.slug)

    # we're returning an HTML response when there are errors so check we don't
    # receive a redirect code
    assert response.status_code == 200

    # confirm we have errors from the signoff formset
    assert response.context_data["signoff_formset"].errors


def test_create_codelist_when_not_logged_in(client):
    p = ProjectFactory()
    csv_data = "code,description\n1067731000000107,Injury whilst swimming (disorder)"
    data = {
        "name": "Test Codelist",
        "coding_system_id": "snomedct",
        "description": "This is a test",
        "methodology": "This is how we did it",
        "csv_data": csv_builder(csv_data),
    }
    rsp = client.post(f"/codelist/{p.slug}/", data, follow=True)
    assertRedirects(rsp, f"/accounts/login/?next=%2Fcodelist%2F{p.slug}%2F")


def test_codelist(client):
    clv = factories.create_published_version()
    cl = clv.codelist
    rsp = client.get(f"/codelist/{cl.project.slug}/{cl.slug}/", follow=True)
    assertRedirects(rsp, f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}/")
    assertContains(rsp, cl.name)


def test_version(client):
    clv = factories.create_published_version()
    cl = clv.codelist
    rsp = client.get(f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}/")
    assertContains(rsp, cl.name)
    assertContains(rsp, cl.description)
    assertContains(rsp, cl.methodology)


def test_version_redirects(client):
    clv = factories.create_published_version()
    cl = clv.codelist
    rsp = client.get(
        f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}-draft/", follow=True
    )
    assertRedirects(rsp, f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}/")
    assertContains(rsp, cl.name)
    assertContains(rsp, cl.description)
    assertContains(rsp, cl.methodology)


def test_draft_version(client):
    clv = factories.create_draft_version()
    cl = clv.codelist
    rsp = client.get(f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}-draft/")
    assertContains(rsp, cl.name)
    assertContains(rsp, cl.description)
    assertContains(rsp, cl.methodology)


def test_draft_version_redirects(client):
    clv = factories.create_draft_version()
    cl = clv.codelist
    rsp = client.get(
        f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}/", follow=True
    )
    assertRedirects(
        rsp, f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}-draft/"
    )
    assertContains(rsp, cl.name)
    assertContains(rsp, cl.description)
    assertContains(rsp, cl.methodology)


def test_download(client):
    clv = factories.create_published_version()
    cl = clv.codelist
    rsp = client.get(
        f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}/download.csv"
    )
    reader = csv.reader(StringIO(rsp.content.decode("utf8")))
    data = list(reader)
    assert data[0] == ["code", "description"]
    assert data[1] == ["1067731000000107", "Injury whilst swimming (disorder)"]


def test_download_does_not_redirect(client):
    clv = factories.create_published_version()
    cl = clv.codelist
    rsp = client.get(
        f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}-draft/download.csv"
    )
    assert rsp.status_code == 404


def test_draft_download(client):
    clv = factories.create_draft_version()
    cl = clv.codelist
    rsp = client.get(
        f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}-draft/download.csv"
    )
    reader = csv.reader(StringIO(rsp.content.decode("utf8")))
    data = list(reader)
    assert data[0] == ["code", "description"]
    assert data[1] == ["1067731000000107", "Injury whilst swimming (disorder)"]


def test_draft_download_does_not_redirect(client):
    clv = factories.create_draft_version()
    cl = clv.codelist
    rsp = client.get(
        f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}/download.csv"
    )
    assert rsp.status_code == 404


def test_versioncreate_missing_field(rf):
    codelist = factories.create_published_version().codelist

    request = rf.post("/", data={})
    request.user = UserFactory()
    response = VersionCreate.as_view()(
        request, project_slug=codelist.project.slug, codelist_slug=codelist.slug,
    )

    assert response.status_code == 200
    assert "form" in response.context_data
    assert len(response.context_data["form"].errors) == 1
    assert "csv_data" in response.context_data["form"].errors


def test_versioncreate_success(rf):
    codelist = factories.create_published_version().codelist

    assert codelist.versions.count() == 1

    csv_data = "code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)"
    data = {
        "csv_data": csv_builder(csv_data),
    }

    request = rf.post("/", data=data)
    request.user = UserFactory()
    response = VersionCreate.as_view()(
        request, project_slug=codelist.project.slug, codelist_slug=codelist.slug,
    )

    assert response.status_code == 302
    assert (
        response.url
        == f"/codelist/{codelist.project.slug}/{codelist.slug}/2020-07-23-a-draft/"
    )

    assert codelist.versions.count() == 2


def test_versioncreate_unknown_codelist(rf):
    codelist = factories.create_codelist()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        VersionCreate.as_view()(
            request, project_slug=codelist.project.slug, codelist_slug="test",
        )


def test_versionpublish_success(rf):
    version = factories.create_draft_version()

    request = rf.post("/")
    request.user = UserFactory()
    response = version_publish(
        request,
        project_slug=version.codelist.project.slug,
        codelist_slug=version.codelist.slug,
        qualified_version_str=version.qualified_version_str,
    )

    assert response.status_code == 302

    version.refresh_from_db()

    assert response.url == version.get_absolute_url()
    assert not version.is_draft


def test_versionpublish_unknown_version(rf):
    codelist = factories.create_codelist()

    request = rf.post("/")
    request.user = UserFactory()
    with pytest.raises(Http404):
        version_publish(
            request,
            project_slug=codelist.project.slug,
            codelist_slug=codelist.slug,
            qualified_version_str="test",
        )


def test_versionpublish_draft_mismatch(rf):
    version = factories.create_published_version()

    # set the version string to that of a draft
    qualified_version_str = f"{version.qualified_version_str}-draft"

    request = rf.post("/")
    request.user = UserFactory()
    response = version_publish(
        request,
        project_slug=version.codelist.project.slug,
        codelist_slug=version.codelist.slug,
        qualified_version_str=qualified_version_str,
    )

    # we should get redirected to the Version page
    assert response.status_code == 302
    assert response.url == version.get_absolute_url()


def test_versionupdate_unknown_version(rf):
    codelist = factories.create_codelist()

    request = rf.get("/")
    request.user = UserFactory()
    with pytest.raises(Http404):
        VersionUpdate.as_view()(
            request,
            project_slug=codelist.project.slug,
            codelist_slug=codelist.slug,
            qualified_version_str="test",
        )


def test_versionupdate_draft_mismatch(rf):
    version = factories.create_published_version()

    # set the version string to that of a draft
    qualified_version_str = f"{version.qualified_version_str}-draft"

    request = rf.get("/")
    request.user = UserFactory()
    response = VersionUpdate.as_view()(
        request,
        project_slug=version.codelist.project.slug,
        codelist_slug=version.codelist.slug,
        qualified_version_str=qualified_version_str,
    )

    # we should get redirected to the Version page
    assert response.status_code == 302
    assert response.url == version.get_absolute_url()


def test_versionupdate_form_error(rf):
    version = factories.create_published_version()

    request = rf.post("/", data={})
    request.user = UserFactory()
    response = VersionUpdate.as_view()(
        request,
        project_slug=version.codelist.project.slug,
        codelist_slug=version.codelist.slug,
        qualified_version_str=version.qualified_version_str,
    )

    assert response.status_code == 200
    assert "form" in response.context_data
    assert "csv_data" in response.context_data["form"].errors


def test_versionupdate_success(rf):
    version = factories.create_draft_version()

    assert version.codelist.versions.count() == 1

    csv_data = "code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)"
    data = {
        "csv_data": csv_builder(csv_data),
    }

    request = rf.post("/", data=data)
    request.user = UserFactory()
    response = VersionUpdate.as_view()(
        request,
        project_slug=version.codelist.project.slug,
        codelist_slug=version.codelist.slug,
        qualified_version_str=version.qualified_version_str,
    )

    assert response.status_code == 302
    assert (
        response.url
        == f"/codelist/{version.codelist.project.slug}/{version.codelist.slug}/2020-07-23-draft/"
    )

    assert version.codelist.versions.count() == 1


def test_versionupdate_not_logged_in(rf):
    version = factories.create_published_version()
    codelist = version.codelist

    assert version.codelist.versions.count() == 1

    request = rf.post("/the/current/url/", data={})
    request.user = AnonymousUser()
    response = VersionUpdate.as_view()(
        request,
        project_slug=codelist.project.slug,
        codelist_slug=codelist.slug,
        qualified_version_str=version.qualified_version_str,
    )

    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/the/current/url/"
