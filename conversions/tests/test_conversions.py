from django.urls import reverse

from codelists.tests.helpers import csv_builder


def test_convert_full_mapping(client, disorder_of_elbow_csv_data):
    data = {
        "from_coding_system_id": "snomedct",
        "to_coding_system_id": "ctv3",
        "csv_data": csv_builder(disorder_of_elbow_csv_data),
        "type": "full",
    }
    response = client.post(reverse("conversions:convert"), data)
    # The response contains the expected headers for both from and to coding systems
    # There are no actual converted codes because we don't have any ctv3 data loaded
    # into the db
    assert (
        response.content.decode() == "snomedct_id,snomedct_name,ctv3_id,ctv3_name\r\n"
    )


def test_convert_to_codes_only(client, disorder_of_elbow_csv_data):
    data = {
        "from_coding_system_id": "snomedct",
        "to_coding_system_id": "ctv3",
        "csv_data": csv_builder(disorder_of_elbow_csv_data),
        "type": "to-codes-only",
    }
    response = client.post(reverse("conversions:convert"), data)
    # The response contains the expected headers for the to coding system only
    # There are no actual converted codes because we don't have any ctv3 data loaded
    # into the db
    assert response.content.decode() == "ctv3_id,ctv3_name\r\n"
