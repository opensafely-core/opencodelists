import csv
from io import BytesIO, StringIO
from unittest.mock import patch

import pytest
from pytest_django.asserts import assertContains, assertRedirects

from codelists.views import CreateCodelist
from opencodelists.tests.factories import ProjectFactory, UserFactory

from . import factories

pytestmark = pytest.mark.freeze_time("2020-07-23")


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
        "csv_data": _build_file_for_upload(csv_data),
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
        "csv_data": _build_file_for_upload(csv_data),
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

    view = CreateCodelist()
    view.setup(request)
    with patch("codelists.views.CreateCodelist.all_valid") as mock_all_valid, patch(
        "codelists.views.CreateCodelist.some_invalid"
    ) as mock_some_invalid:
        view.post(request)

    # was the error handler, some_invalid, called?
    # we're not doing any custom error handling in the form or formsets so no
    # need to test what Django is already testing
    mock_all_valid.assert_not_called()
    mock_some_invalid.assert_called_once()


def test_create_codelist_when_not_logged_in(client):
    p = ProjectFactory()
    csv_data = "code,description\n1067731000000107,Injury whilst swimming (disorder)"
    data = {
        "name": "Test Codelist",
        "coding_system_id": "snomedct",
        "description": "This is a test",
        "methodology": "This is how we did it",
        "csv_data": _build_file_for_upload(csv_data),
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


def test_create_version(logged_in_client):
    clv = factories.create_published_version()
    cl = clv.codelist
    csv_data = "code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)"
    data = {
        "csv_data": _build_file_for_upload(csv_data),
    }
    rsp = logged_in_client.post(
        f"/codelist/{cl.project.slug}/{cl.slug}/", data, follow=True
    )
    assertRedirects(rsp, f"/codelist/{cl.project.slug}/{cl.slug}/2020-07-23-a-draft/")


def test_create_version_when_not_logged_in(client):
    clv = factories.create_published_version()
    cl = clv.codelist
    csv_data = "code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)"
    data = {
        "csv_data": _build_file_for_upload(csv_data),
    }
    rsp = client.post(f"/codelist/{cl.project.slug}/{cl.slug}/", data, follow=True)
    assertRedirects(
        rsp, f"/accounts/login/?next=%2Fcodelist%2F{cl.project.slug}%2F{cl.slug}%2F"
    )


def test_update_version(logged_in_client):
    clv = factories.create_draft_version()
    cl = clv.codelist
    csv_data = "code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)"
    data = {
        "csv_data": _build_file_for_upload(csv_data),
    }
    rsp = logged_in_client.post(
        f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}-draft/",
        data,
        follow=True,
    )
    assertRedirects(
        rsp, f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}-draft/"
    )


def test_update_version_when_not_logged_in(client):
    clv = factories.create_draft_version()
    cl = clv.codelist
    csv_data = "code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)"
    data = {
        "csv_data": _build_file_for_upload(csv_data),
    }
    rsp = client.post(
        f"/codelist/{cl.project.slug}/{cl.slug}/{clv.version_str}-draft/",
        data,
        follow=True,
    )
    assertRedirects(
        rsp,
        f"/accounts/login/?next=%2Fcodelist%2F{cl.project.slug}%2F{cl.slug}%2F{clv.version_str}-draft%2F",
    )


def _build_file_for_upload(contents):
    buffer = BytesIO()
    buffer.write(contents.encode("utf8"))
    buffer.seek(0)
    return buffer
