import json

from opencodelists.tests.assertions import assert_difference, assert_no_difference


def test_codelists(client, organisation):
    rsp = client.get(f"/api/v1/codelist/{organisation.slug}/")
    data = json.loads(rsp.content)
    assert rsp.status_code == 200
    assert data["codelists"] == [
        {
            "full_slug": "test-university/old-style-codelist",
            "slug": "old-style-codelist",
            "name": "Old-style Codelist",
            "versions": [
                {
                    "hash": "66f08cca",
                    "tag": None,
                    "full_slug": "test-university/old-style-codelist/66f08cca",
                },
                {
                    "hash": "4de11995",
                    "tag": None,
                    "full_slug": "test-university/old-style-codelist/4de11995",
                },
            ],
        },
        {
            "full_slug": "test-university/new-style-codelist",
            "slug": "new-style-codelist",
            "name": "New-style Codelist",
            "versions": [
                {
                    "hash": "34d1a660",
                    "tag": None,
                    "full_slug": "test-university/new-style-codelist/34d1a660",
                },
                {
                    "hash": "1bc2332b",
                    "tag": None,
                    "full_slug": "test-university/new-style-codelist/1bc2332b",
                },
                {
                    "hash": "02b2bff6",
                    "tag": None,
                    "full_slug": "test-university/new-style-codelist/02b2bff6",
                },
            ],
        },
        {
            "full_slug": "test-university/codelist-from-scratch",
            "slug": "codelist-from-scratch",
            "name": "Codelist From Scratch",
            "versions": [
                {
                    "hash": "69a34cc0",
                    "tag": None,
                    "full_slug": "test-university/codelist-from-scratch/69a34cc0",
                }
            ],
        },
    ]


def test_codelists_post(client, user):
    data = {
        "name": "New codelist",
        "coding_system_id": "snomedct",
        "codes": ["128133004", "156659008"],
    }

    with assert_difference(user.codelists.count, expected_difference=1):
        rsp = post(client, user.get_codelists_api_url(), data, user)

    assert rsp.status_code == 200


def test_codelists_post_no_auth(client, user):
    data = {
        "name": "New codelist",
        "coding_system_id": "snomedct",
        "codes": ["128133004", "156659008"],
    }

    with assert_no_difference(user.codelists.count):
        rsp = post(client, user.get_codelists_api_url(), data, None)

    assert rsp.status_code == 401


def test_codelists_post_permission_denied(client, user, user_without_organisation):
    data = {
        "name": "New codelist",
        "coding_system_id": "snomedct",
        "codes": ["128133004", "156659008"],
    }

    with assert_no_difference(user.codelists.count):
        rsp = post(
            client, user.get_codelists_api_url(), data, user_without_organisation
        )

    assert rsp.status_code == 403


def test_versions_post_codes(client, user, user_codelist):
    data = {"codes": ["128133004", "156659008"]}

    with assert_difference(user_codelist.versions.count, expected_difference=1):
        rsp = post(client, user_codelist.get_versions_api_url(), data, user)

    assert rsp.status_code == 200


def test_versions_post_ecl(client, user, user_codelist):
    data = {"ecl": "<<128133004 OR 156659008"}

    with assert_difference(user_codelist.versions.count, expected_difference=1):
        rsp = post(client, user_codelist.get_versions_api_url(), data, user)

    assert rsp.status_code == 200


def test_versions_post_no_difference(client, user, user_codelist):
    data = {"ecl": "(<<128133004 OR 156659008) MINUS <<439656005"}

    with assert_no_difference(user_codelist.versions.count):
        rsp = post(client, user_codelist.get_versions_api_url(), data, user)

    assert rsp.status_code == 400
    assert json.loads(rsp.content) == {"error": "No difference to previous version"}


def test_versions_post_bad_ecl(client, user, user_codelist):
    data = {"ecl": "<<128133004 MIN"}

    with assert_no_difference(user_codelist.versions.count):
        rsp = post(client, user_codelist.get_versions_api_url(), data, user)

    assert rsp.status_code == 400
    assert json.loads(rsp.content)["error"].startswith("InputMismatchException")


def test_versions_post_missing_data(client, user, user_codelist):
    data = {}

    with assert_no_difference(user_codelist.versions.count):
        rsp = post(client, user_codelist.get_versions_api_url(), data, user)

    assert rsp.status_code == 400
    assert json.loads(rsp.content) == {
        "error": "Provide exactly one of `codes` or `ecl`"
    }


def test_versions_post_no_auth(client, user_codelist):
    data = {"ecl": "<<128133004"}

    with assert_no_difference(user_codelist.versions.count):
        rsp = post(client, user_codelist.get_versions_api_url(), data, None)

    assert rsp.status_code == 401


def test_versions_post_permission_denied(
    client, user_without_organisation, user_codelist
):
    data = {"ecl": "<<128133004"}

    with assert_no_difference(user_codelist.versions.count):
        rsp = post(
            client,
            user_codelist.get_versions_api_url(),
            data,
            user_without_organisation,
        )

    assert rsp.status_code == 403


def post(client, url, data, user):
    if user is None:
        headers = {}
    else:
        headers = {"HTTP_AUTHORIZATION": f"Token {user.api_token}"}
    return client.post(url, data, content_type="application/json", **headers)
