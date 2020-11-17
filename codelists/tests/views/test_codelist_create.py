from codelists.actions import create_codelist
from opencodelists.tests.factories import OrganisationFactory, UserFactory

from ..helpers import csv_builder
from .assertions import (
    assert_get_unauthenticated,
    assert_get_unauthorised,
    assert_post_unauthenticated,
    assert_post_unauthorised,
)


def test_get_unauthenticated(client):
    organisation = OrganisationFactory()
    assert_get_unauthenticated(client, organisation.get_codelist_create_url())


def test_post_unauthenticated(client):
    organisation = OrganisationFactory()
    assert_post_unauthenticated(client, organisation.get_codelist_create_url())


def test_get_unauthorised(client):
    organisation = OrganisationFactory()
    assert_get_unauthorised(client, organisation.get_codelist_create_url())


def test_post_unauthorised(client):
    organisation = OrganisationFactory()
    assert_post_unauthorised(client, organisation.get_codelist_create_url())


def test_post_success(client):
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

    client.force_login(organisation.regular_user)
    response = client.post(organisation.get_codelist_create_url(), data=data)

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


def test_post_invalid(client):
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

    client.force_login(organisation.regular_user)
    response = client.post(organisation.get_codelist_create_url(), data=data)

    # we're returning an HTML response when there are errors so check we don't
    # receive a redirect code
    assert response.status_code == 200

    # confirm we have errors from the signoff formset
    assert response.context_data["signoff_formset"].errors


def test_post_with_duplicate_name(client):
    organisation = OrganisationFactory()

    create_codelist(
        owner=organisation,
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

    client.force_login(organisation.regular_user)
    response = client.post(organisation.get_codelist_create_url(), data=data)

    assert organisation.codelists.count() == 1

    # we're returning an HTML response when there are errors so check we don't
    # receive a redirect code
    assert response.status_code == 200

    # confirm we have errors from the codelist form
    assert response.context_data["codelist_form"].errors == {
        "__all__": ["There is already a codelist called Test"]
    }
