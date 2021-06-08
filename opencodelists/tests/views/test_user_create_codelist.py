from codelists.models import Codelist
from codelists.tests.helpers import csv_builder

from ..assertions import assert_difference, assert_no_difference


def test_get_for_organisation_user(client, organisation_user):
    client.force_login(organisation_user)
    response = client.get("/users/bob/new-codelist/")
    assert response.status_code == 200


def test_get_for_user_without_organisation(client, user_without_organisation):
    client.force_login(user_without_organisation)
    response = client.get("/users/dave/new-codelist/")
    assert response.status_code == 200


def test_post_with_csv(client, organisation_user, disorder_of_elbow_csv_data_no_header):
    client.force_login(organisation_user)
    data = {
        "name": "Test",
        "coding_system_id": "snomedct",
        "owner": "user:bob",
        "csv_data": csv_builder(disorder_of_elbow_csv_data_no_header),
    }

    with assert_difference(Codelist.objects.count, expected_difference=1):
        response = client.post("/users/bob/new-codelist/", data, follow=True)

    codelist = organisation_user.codelists.get(handles__name="Test")
    version = codelist.versions.get()

    assert response.redirect_chain[-1][0] == version.get_absolute_url()
    assert version.is_published


def test_post_without_csv(client, organisation_user):
    client.force_login(organisation_user)
    data = {
        "name": "Test",
        "coding_system_id": "snomedct",
        "owner": "user:bob",
    }

    with assert_difference(Codelist.objects.count, expected_difference=1):
        response = client.post("/users/bob/new-codelist/", data, follow=True)

    codelist = organisation_user.codelists.get(handles__name="Test")
    version = codelist.versions.get()

    assert response.redirect_chain[-1][0] == version.get_builder_url("draft")
    assert version.is_draft


def test_post_create_organisation_codelist(client, organisation_user, organisation):
    client.force_login(organisation_user)
    data = {
        "name": "Test",
        "coding_system_id": "snomedct",
        "owner": "organisation:test-university",
    }

    with assert_difference(Codelist.objects.count, expected_difference=1):
        response = client.post("/users/bob/new-codelist/", data, follow=True)

    codelist = organisation.codelists.get(handles__name="Test")
    version = codelist.versions.get()

    assert response.redirect_chain[-1][0] == version.get_builder_url("draft")
    assert version.is_draft


def test_post_invalid_with_csv(client, organisation_user):
    client.force_login(organisation_user)
    csv_data = "256307007,Banana (substance)"
    data = {
        "name": "Test",
        "coding_system_id": "snomedct",
        "owner": "user:bob",
        "csv_data": csv_builder(csv_data),
    }

    with assert_no_difference(Codelist.objects.count):
        response = client.post("/users/bob/new-codelist/", data)

    assert b"CSV file contains 1 unknown code (256307007) on line 1" in response.content


def test_post_invalid_duplicate_name(client, organisation_user):
    client.force_login(organisation_user)
    data = {
        "name": "User-owned Codelist",
        "coding_system_id": "snomedct",
        "owner": "user:bob",
    }

    with assert_no_difference(Codelist.objects.count):
        response = client.post("/users/bob/new-codelist/", data)

    assert b"There is already a codelist called User-owned Codelist" in response.content
