import json

from opencodelists.tests.assertions import assert_difference, assert_no_difference


def test_codelists_get(client, organisation):
    rsp = client.get(f"/api/v1/codelist/{organisation.slug}/")
    data = json.loads(rsp.content)
    assert rsp.status_code == 200
    assert data["codelists"] == [
        {
            "full_slug": "test-university/codelist-from-scratch",
            "slug": "codelist-from-scratch",
            "name": "Codelist From Scratch",
            "organisation": "Test University",
            "coding_system_id": "snomedct",
            "versions": [
                {
                    "hash": "69a34cc0",
                    "tag": None,
                    "full_slug": "test-university/codelist-from-scratch/69a34cc0",
                    "status": "draft",
                }
            ],
        },
        {
            "full_slug": "test-university/minimal-codelist",
            "slug": "minimal-codelist",
            "name": "Minimal Codelist",
            "organisation": "Test University",
            "coding_system_id": "snomedct",
            "versions": [
                {
                    "hash": "1e74f321",
                    "tag": None,
                    "full_slug": "test-university/minimal-codelist/1e74f321",
                    "status": "published",
                },
                {
                    "hash": "05657fec",
                    "tag": None,
                    "full_slug": "test-university/minimal-codelist/05657fec",
                    "status": "draft",
                },
            ],
        },
        {
            "full_slug": "test-university/new-style-codelist",
            "slug": "new-style-codelist",
            "name": "New-style Codelist",
            "organisation": "Test University",
            "coding_system_id": "snomedct",
            "versions": [
                {
                    "hash": "34d1a660",
                    "tag": None,
                    "full_slug": "test-university/new-style-codelist/34d1a660",
                    "status": "published",
                },
                {
                    "hash": "1bc2332b",
                    "tag": None,
                    "full_slug": "test-university/new-style-codelist/1bc2332b",
                    "status": "under review",
                },
                {
                    "hash": "02b2bff6",
                    "tag": None,
                    "full_slug": "test-university/new-style-codelist/02b2bff6",
                    "status": "under review",
                },
            ],
        },
        {
            "full_slug": "test-university/old-style-codelist",
            "slug": "old-style-codelist",
            "name": "Old-style Codelist",
            "organisation": "Test University",
            "coding_system_id": "snomedct",
            "versions": [
                {
                    "hash": "66f08cca",
                    "tag": None,
                    "full_slug": "test-university/old-style-codelist/66f08cca",
                    "status": "under review",
                },
                {
                    "hash": "4de11995",
                    "tag": None,
                    "full_slug": "test-university/old-style-codelist/4de11995",
                    "status": "under review",
                },
            ],
        },
    ]


def test_codelists_get_with_coding_system_id(client, organisation):
    rsp = client.get(f"/api/v1/codelist/{organisation.slug}/?coding_system_id=snomedct")
    data = json.loads(rsp.content)
    assert len(data["codelists"]) == 4

    rsp = client.get(f"/api/v1/codelist/{organisation.slug}/?coding_system_id=")
    data = json.loads(rsp.content)
    assert len(data["codelists"]) == 4

    rsp = client.get(f"/api/v1/codelist/{organisation.slug}/?coding_system_id=bnf")
    data = json.loads(rsp.content)
    assert len(data["codelists"]) == 0


def test_codelists_get_with_no_organisation(client, organisation):
    rsp = client.get("/api/v1/codelist/?coding_system_id=snomedct")
    data = json.loads(rsp.content)
    user_codelists = [
        cl for cl in data["codelists"] if cl["full_slug"].startswith("user")
    ]
    assert len(user_codelists) == 2
    for user_codelist in user_codelists:
        assert user_codelist["organisation"] == ""


def test_codelists_get_with_tag(client, universe):
    rsp = client.get("/api/v1/codelist/?tag=new-style")
    data = json.loads(rsp.content)
    assert len(data["codelists"]) == 4


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


def test_versions_post_codes_with_no_force_new_version(client, user, user_codelist):
    data = {
        "name": "New codelist",
        "coding_system_id": "snomedct",
        "codes": ["128133004", "156659008"],
    }
    post(client, user_codelist.get_versions_api_url(), data, user)

    same_data = {
        "name": "New codelist",
        "codes": ["128133004", "156659008"],
        "always_create_new_version": False,
    }
    with assert_no_difference(user_codelist.versions.count):
        rsp = post(client, user_codelist.get_versions_api_url(), same_data, user)

    assert rsp.status_code == 400


def test_versions_post_codes_with_force_new_version(client, user, user_codelist):
    data = {
        "name": "New codelist",
        "coding_system_id": "snomedct",
        "codes": ["128133004", "156659008"],
    }
    post(client, user_codelist.get_versions_api_url(), data, user)

    same_data = {
        "name": "New codelist",
        "codes": ["128133004", "156659008"],
        "always_create_new_version": True,
    }
    with assert_difference(user_codelist.versions.count, expected_difference=1):
        rsp = post(client, user_codelist.get_versions_api_url(), same_data, user)

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
