import csv
import datetime
from io import StringIO

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from pytest_django.asserts import assertContains, assertRedirects

from codelists.actions import create_codelist, publish_version
from codelists.views import (
    VersionCreate,
    VersionUpdate,
    codelist,
    codelist_create,
    codelist_update,
    version,
    version_publish,
)
from opencodelists.tests.factories import OrganisationFactory, UserFactory

from .factories import (
    CodelistFactory,
    ReferenceFactory,
    SignOffFactory,
    create_draft_version,
    create_published_version,
)
from .helpers import csv_builder

pytestmark = [
    pytest.mark.freeze_time("2020-07-23"),
    pytest.mark.filterwarnings(
        "ignore::DeprecationWarning:bleach",
        "ignore::django.utils.deprecation.RemovedInDjango40Warning:debug_toolbar",
    ),
]


def test_codelistcreate_success(rf):
    organisation = OrganisationFactory()
    signoff_user = UserFactory()

    assert organisation.codelists.count() == 0

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
    response = codelist_create(request, organisation_slug=organisation.slug)

    assert response.status_code == 302
    assert response.url == f"/codelist/{organisation.slug}/test-codelist/"

    assert organisation.codelists.count() == 1
    codelist = organisation.codelists.first()
    assert codelist.name == "Test Codelist"

    # we should have one reference to example.com
    assert codelist.references.count() == 1
    ref = codelist.references.first()
    assert ref.url == "http://example.com"

    # we should have one signoff by signoff user
    assert codelist.signoffs.count() == 1
    signoff = codelist.signoffs.first()
    assert signoff.user == signoff_user


def test_codelistcreate_invalid_post(rf):
    organisation = OrganisationFactory()
    signoff_user = UserFactory()

    assert organisation.codelists.count() == 0

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
    response = codelist_create(request, organisation_slug=organisation.slug)

    # we're returning an HTML response when there are errors so check we don't
    # receive a redirect code
    assert response.status_code == 200

    # confirm we have errors from the signoff formset
    assert response.context_data["signoff_formset"].errors


def test_codelistcreate_when_not_logged_in(client):
    p = OrganisationFactory()
    csv_data = "code,description\n1067731000000107,Injury whilst swimming (disorder)"
    data = {
        "name": "Test Codelist",
        "coding_system_id": "snomedct",
        "description": "This is a test",
        "methodology": "This is how we did it",
        "csv_data": csv_builder(csv_data),
    }
    rsp = client.post(f"/codelist/{p.slug}/add/", data, follow=True)
    assertRedirects(rsp, f"/accounts/login/?next=%2Fcodelist%2F{p.slug}%2Fadd%2F")


def test_codelistcreate_with_duplicate_name(rf):
    organisation = OrganisationFactory()

    create_codelist(
        organisation=organisation,
        name="Test",
        coding_system_id="snomedct",
        description="This is a test",
        methodology="This is how we did it",
        csv_data="code,description\n1067731000000107,Injury whilst swimming (disorder)",
    )

    assert organisation.codelists.count() == 1

    csv_data = "code,description\n1067731000000107,Injury whilst swimming (disorder)"
    data = {
        "name": "Test",
        "coding_system_id": "snomedct",
        "description": "This is a test",
        "methodology": "This is how we did it",
        "csv_data": csv_builder(csv_data),
        "reference-TOTAL_FORMS": "0",
        "reference-INITIAL_FORMS": "0",
        "reference-MIN_NUM_FORMS": "0",
        "reference-MAX_NUM_FORMS": "1000",
        "signoff-TOTAL_FORMS": "0",
        "signoff-INITIAL_FORMS": "0",
        "signoff-MIN_NUM_FORMS": "0",
        "signoff-MAX_NUM_FORMS": "1000",
    }

    request = rf.post("/", data=data)
    request.user = UserFactory()
    response = codelist_create(request, organisation_slug=organisation.slug)

    assert organisation.codelists.count() == 1

    # we're returning an HTML response when there are errors so check we don't
    # receive a redirect code
    assert response.status_code == 200

    # confirm we have errors from the codelist form
    assert response.context_data["codelist_form"].errors == {
        "__all__": ["There is already a codelist in this organisation called Test"]
    }


def test_codelistupdate_invalid_post(rf):
    codelist = CodelistFactory()
    signoff_1 = SignOffFactory(codelist=codelist)
    reference_1 = ReferenceFactory(codelist=codelist)

    # missing signoff-0-date
    data = {
        "organisation": codelist.organisation.slug,
        "name": "Test Codelist",
        "coding_system_id": "snomedct",
        "description": "This is a test",
        "methodology": "This is how we did it",
        "reference-TOTAL_FORMS": "1",
        "reference-INITIAL_FORMS": "0",
        "reference-MIN_NUM_FORMS": "0",
        "reference-MAX_NUM_FORMS": "1000",
        "reference-0-text": reference_1.text,
        "reference-0-url": reference_1.url,
        "signoff-TOTAL_FORMS": "1",
        "signoff-INITIAL_FORMS": "0",
        "signoff-MIN_NUM_FORMS": "0",
        "signoff-MAX_NUM_FORMS": "1000",
        "signoff-0-user": signoff_1.user.username,
    }

    request = rf.post("/", data=data)
    request.user = UserFactory()
    response = codelist_update(
        request,
        organisation_slug=codelist.organisation.slug,
        codelist_slug=codelist.slug,
    )

    # we're returning an HTML response when there are errors so check we don't
    # receive a redirect code
    assert response.status_code == 200

    # confirm we have errors from the signoff formset
    assert response.context_data["signoff_formset"].errors


def test_codelistupdate_success_get(rf):
    codelist = CodelistFactory()
    SignOffFactory(codelist=codelist)
    SignOffFactory(codelist=codelist)
    ReferenceFactory(codelist=codelist)
    ReferenceFactory(codelist=codelist)

    request = rf.get("/")
    request.user = UserFactory()
    response = codelist_update(
        request,
        organisation_slug=codelist.organisation.slug,
        codelist_slug=codelist.slug,
    )

    assert response.status_code == 200

    form = response.context_data["codelist_form"]
    assert form.data["name"] == codelist.name
    assert form.data["organisation"] == codelist.organisation
    assert form.data["coding_system_id"] == codelist.coding_system_id
    assert form.data["description"] == codelist.description
    assert form.data["methodology"] == codelist.methodology


def test_codelistupdate_success_post(rf):
    codelist = CodelistFactory()
    signoff_1 = SignOffFactory(codelist=codelist)
    signoff_2 = SignOffFactory(codelist=codelist)
    reference_1 = ReferenceFactory(codelist=codelist)
    reference_2 = ReferenceFactory(codelist=codelist)

    assert codelist.references.count() == 2
    assert codelist.signoffs.count() == 2

    new_signoff_user = UserFactory()

    data = {
        "organisation": codelist.organisation.slug,
        "name": "Test Codelist",
        "coding_system_id": "snomedct",
        "description": "This is a test CHANGED",
        "methodology": "This is how we did it",
        "reference-TOTAL_FORMS": "3",
        "reference-INITIAL_FORMS": "2",
        "reference-MIN_NUM_FORMS": "0",
        "reference-MAX_NUM_FORMS": "1000",
        "reference-0-text": reference_1.text,
        "reference-0-url": reference_1.url,
        "reference-0-id": reference_1.id,
        "reference-0-DELETE": "on",
        "reference-1-text": reference_2.text + " CHANGED",
        "reference-1-url": reference_2.url,
        "reference-1-id": reference_2.id,
        "reference-2-text": "This is a new reference",
        "reference-2-url": "http://example.com",
        "signoff-TOTAL_FORMS": "3",
        "signoff-INITIAL_FORMS": "2",
        "signoff-MIN_NUM_FORMS": "0",
        "signoff-MAX_NUM_FORMS": "1000",
        "signoff-0-user": signoff_1.user.username,
        "signoff-0-date": signoff_1.date,
        "signoff-0-id": signoff_1.id,
        "signoff-0-DELETE": "on",
        "signoff-1-user": signoff_2.user.username,
        "signoff-1-date": signoff_2.date + datetime.timedelta(days=2),
        "signoff-1-id": signoff_2.id,
        "signoff-2-user": new_signoff_user.username,
        "signoff-2-date": "2000-01-01",
    }

    request = rf.post("/", data=data)
    request.user = UserFactory()
    response = codelist_update(
        request,
        organisation_slug=codelist.organisation.slug,
        codelist_slug=codelist.slug,
    )

    assert response.status_code == 302
    assert response.url == f"/codelist/{codelist.organisation.slug}/{codelist.slug}/"

    # we should have still have 2 references but the first should be changed
    # while the second is new.
    assert codelist.references.count() == 2
    assert codelist.references.first().text == reference_2.text + " CHANGED"
    assert codelist.references.last().text == "This is a new reference"

    # we should have still have 2 signoffs but the first should be changed
    # while the second is new.
    assert codelist.signoffs.count() == 2
    assert codelist.signoffs.first().date == signoff_2.date + datetime.timedelta(days=2)
    assert codelist.signoffs.last().user == new_signoff_user


def test_codelistupdate_when_not_logged_in(rf):
    codelist = CodelistFactory()

    request = rf.post("/the/current/url/")
    request.user = AnonymousUser()
    response = codelist_update(
        request,
        organisation_slug=codelist.organisation.slug,
        codelist_slug=codelist.slug,
    )

    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/the/current/url/"


def test_codelistupdate_with_duplicate_name(rf):
    organisation = OrganisationFactory()

    CodelistFactory(name="Existing Codelist", organisation=organisation)
    codelist = CodelistFactory(organisation=organisation)

    data = {
        "organisation": codelist.organisation.slug,
        "name": "Existing Codelist",
        "coding_system_id": "snomedct",
        "description": "This is a test CHANGED",
        "methodology": "This is how we did it",
        "reference-TOTAL_FORMS": "0",
        "reference-INITIAL_FORMS": "0",
        "reference-MIN_NUM_FORMS": "0",
        "reference-MAX_NUM_FORMS": "1000",
        "signoff-TOTAL_FORMS": "0",
        "signoff-INITIAL_FORMS": "0",
        "signoff-MIN_NUM_FORMS": "0",
        "signoff-MAX_NUM_FORMS": "1000",
    }

    request = rf.post("/", data=data)
    request.user = UserFactory()
    response = codelist_update(
        request,
        organisation_slug=codelist.organisation.slug,
        codelist_slug=codelist.slug,
    )

    assert response.status_code == 200

    # confirm we have errors from the codelist form
    assert response.context_data["codelist_form"].errors == {
        "__all__": [
            "There is already a codelist in this organisation called Existing Codelist"
        ]
    }


def test_codelist(rf):
    clv = create_published_version()
    cl = clv.codelist

    request = rf.get("/")
    response = codelist(request, cl.organisation.slug, cl.slug)

    # check codelist() redirects to the correct version page
    assert response.status_code == 302
    assert (
        response.url == f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.version_str}/"
    )


def test_version(client, tennis_elbow_codelist):
    cl = tennis_elbow_codelist
    clv = publish_version(version=cl.versions.first())
    rsp = client.get(f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.version_str}/")
    assertContains(rsp, cl.name)
    assertContains(rsp, cl.description)
    assertContains(rsp, cl.methodology)


def test_version_redirects(rf):
    clv = create_published_version()
    cl = clv.codelist
    request = rf.get("/")
    response = version(
        request, cl.organisation.slug, cl.slug, f"{clv.version_str}-draft"
    )

    # check version() redirects to the non-draft page for a published version
    assert response.status_code == 302
    assert (
        response.url == f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.version_str}/"
    )


def test_draft_version(client, tennis_elbow_codelist):
    cl = tennis_elbow_codelist
    clv = cl.versions.first()
    rsp = client.get(
        f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.version_str}-draft/"
    )
    assertContains(rsp, cl.name)
    assertContains(rsp, cl.description)
    assertContains(rsp, cl.methodology)


def test_draft_version_redirects(rf):
    clv = create_draft_version()
    cl = clv.codelist
    request = rf.get("/")
    response = version(request, cl.organisation.slug, cl.slug, clv.version_str)

    # check version() redirects to the draft page for a draft version
    assert response.status_code == 302

    expected = f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.version_str}-draft/"
    assert response.url == expected


def test_download(client):
    clv = create_published_version()
    cl = clv.codelist
    rsp = client.get(
        f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.version_str}/download.csv"
    )
    reader = csv.reader(StringIO(rsp.content.decode("utf8")))
    data = list(reader)
    assert data[0] == ["code", "description"]
    assert data[1] == ["1067731000000107", "Injury whilst swimming (disorder)"]


def test_download_does_not_redirect(client):
    clv = create_published_version()
    cl = clv.codelist
    rsp = client.get(
        f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.version_str}-draft/download.csv"
    )
    assert rsp.status_code == 404


def test_draft_download(client):
    clv = create_draft_version()
    cl = clv.codelist
    rsp = client.get(
        f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.version_str}-draft/download.csv"
    )
    reader = csv.reader(StringIO(rsp.content.decode("utf8")))
    data = list(reader)
    assert data[0] == ["code", "description"]
    assert data[1] == ["1067731000000107", "Injury whilst swimming (disorder)"]


def test_draft_download_does_not_redirect(client):
    clv = create_draft_version()
    cl = clv.codelist
    rsp = client.get(
        f"/codelist/{cl.organisation.slug}/{cl.slug}/{clv.version_str}/download.csv"
    )
    assert rsp.status_code == 404


def test_versioncreate_missing_field(rf):
    codelist = create_published_version().codelist

    request = rf.post("/", data={})
    request.user = UserFactory()
    response = VersionCreate.as_view()(
        request,
        organisation_slug=codelist.organisation.slug,
        codelist_slug=codelist.slug,
    )

    assert response.status_code == 200
    assert "form" in response.context_data
    assert len(response.context_data["form"].errors) == 1
    assert "csv_data" in response.context_data["form"].errors


def test_versioncreate_success(rf):
    codelist = create_published_version().codelist

    assert codelist.versions.count() == 1

    csv_data = "code,description\n1068181000000106, Injury whilst synchronised swimming (disorder)"
    data = {
        "csv_data": csv_builder(csv_data),
    }

    request = rf.post("/", data=data)
    request.user = UserFactory()
    response = VersionCreate.as_view()(
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


def test_versioncreate_unknown_codelist(rf):
    codelist = CodelistFactory()

    request = rf.get("/")
    request.user = UserFactory()

    with pytest.raises(Http404):
        VersionCreate.as_view()(
            request, organisation_slug=codelist.organisation.slug, codelist_slug="test"
        )


def test_versionpublish_success(rf):
    version = create_draft_version()

    request = rf.post("/")
    request.user = UserFactory()
    response = version_publish(
        request,
        organisation_slug=version.codelist.organisation.slug,
        codelist_slug=version.codelist.slug,
        qualified_version_str=version.qualified_version_str,
    )

    assert response.status_code == 302

    version.refresh_from_db()

    assert response.url == version.get_absolute_url()
    assert not version.is_draft


def test_versionpublish_unknown_version(rf):
    codelist = CodelistFactory()

    request = rf.post("/")
    request.user = UserFactory()
    with pytest.raises(Http404):
        version_publish(
            request,
            organisation_slug=codelist.organisation.slug,
            codelist_slug=codelist.slug,
            qualified_version_str="test",
        )


def test_versionpublish_draft_mismatch(rf):
    version = create_published_version()

    # set the version string to that of a draft
    qualified_version_str = f"{version.qualified_version_str}-draft"

    request = rf.post("/")
    request.user = UserFactory()
    response = version_publish(
        request,
        organisation_slug=version.codelist.organisation.slug,
        codelist_slug=version.codelist.slug,
        qualified_version_str=qualified_version_str,
    )

    # we should get redirected to the Version page
    assert response.status_code == 302
    assert response.url == version.get_absolute_url()


def test_versionupdate_unknown_version(rf):
    codelist = CodelistFactory()

    request = rf.get("/")
    request.user = UserFactory()
    with pytest.raises(Http404):
        VersionUpdate.as_view()(
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
    response = VersionUpdate.as_view()(
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
    response = VersionUpdate.as_view()(
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
    response = VersionUpdate.as_view()(
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
    response = VersionUpdate.as_view()(
        request,
        organisation_slug=codelist.organisation.slug,
        codelist_slug=codelist.slug,
        qualified_version_str=version.qualified_version_str,
    )

    assert response.status_code == 302
    assert response.url == "/accounts/login/?next=/the/current/url/"
