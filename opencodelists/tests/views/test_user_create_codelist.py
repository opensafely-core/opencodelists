from codelists.tests.helpers import csv_builder

from ..factories import UserFactory


def test_get(client):
    user = UserFactory()
    client.force_login(user)

    response = client.get(f"/users/{user.username}/new-codelist/")

    assert response.status_code == 200


def test_post_valid_with_csv(client, tennis_elbow):
    user = UserFactory()
    client.force_login(user)

    csv_data = "239964003,Soft tissue lesion of elbow region (disorder)"
    data = {
        "name": "Test",
        "coding_system_id": "snomedct",
        "owner": user.username,
        "csv_data": csv_builder(csv_data),
    }
    response = client.post(f"/users/{user.username}/new-codelist/", data, follow=True)

    assert response.redirect_chain[-1][0] != f"/codelist/user/{user.username}/test/"
    assert response.redirect_chain[-1][0].startswith(
        f"/codelist/user/{user.username}/test/"
    )


def test_post_valid_without_csv(client):
    user = UserFactory()
    client.force_login(user)

    data = {
        "name": "Test",
        "coding_system_id": "snomedct",
        "owner": user.username,
    }
    response = client.post(f"/users/{user.username}/new-codelist/", data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain[-1][0].startswith("/builder/")


def test_post_invalid_with_csv(client, tennis_elbow):
    user = UserFactory()
    client.force_login(user)

    csv_data = "256307007,Banana (substance)"
    data = {
        "name": "Test",
        "coding_system_id": "snomedct",
        "owner": user.username,
        "csv_data": csv_builder(csv_data),
    }
    response = client.post(f"/users/{user.username}/new-codelist/", data)

    assert b"CSV file contains 1 unknown code (256307007) on line 1" in response.content


def test_post_duplicate_name(client):
    user = UserFactory()
    client.force_login(user)

    data = {
        "name": "Test",
        "coding_system_id": "snomedct",
        "owner": user.username,
    }
    client.post(f"/users/{user.username}/new-codelist/", data)

    response = client.post(f"/users/{user.username}/new-codelist/", data)
    assert b"There is already a codelist called Test" in response.content
