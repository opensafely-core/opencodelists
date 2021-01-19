import json

from opencodelists.tests.assertions import assert_difference, assert_no_difference


def test_versions_post(client, user, user_codelist):
    data = {"ecl": "<<128133004"}
    headers = {"HTTP_AUTHORIZATION": f"Token {user.api_token}"}

    with assert_difference(user_codelist.versions.count, expected_difference=1):
        rsp = client.post(user_codelist.get_versions_api_url(), data, **headers)

    assert rsp.status_code == 200


def test_versions_post_no_difference(client, user, user_codelist):
    data = {"ecl": "<<128133004 MINUS <<439656005"}
    headers = {"HTTP_AUTHORIZATION": f"Token {user.api_token}"}

    with assert_no_difference(user_codelist.versions.count):
        rsp = client.post(user_codelist.get_versions_api_url(), data, **headers)

    assert rsp.status_code == 400
    assert json.loads(rsp.content) == {"error": "No difference to previous version"}


def test_versions_post_bad_ecl(client, user, user_codelist):
    data = {"ecl": "<<128133004 MIN"}
    headers = {"HTTP_AUTHORIZATION": f"Token {user.api_token}"}

    with assert_no_difference(user_codelist.versions.count):
        rsp = client.post(user_codelist.get_versions_api_url(), data, **headers)

    assert rsp.status_code == 400
    assert json.loads(rsp.content)["error"].startswith("InputMismatchException")


def test_versions_post_missing_ecl(client, user, user_codelist):
    data = {}
    headers = {"HTTP_AUTHORIZATION": f"Token {user.api_token}"}

    with assert_no_difference(user_codelist.versions.count):
        rsp = client.post(user_codelist.get_versions_api_url(), data, **headers)

    assert rsp.status_code == 400
    assert json.loads(rsp.content) == {"error": "Missing `ecl` key"}


def test_versions_post_no_auth(client, user_codelist):
    data = {"ecl": "<<128133004"}

    with assert_no_difference(user_codelist.versions.count):
        rsp = client.post(user_codelist.get_versions_api_url(), data)

    assert rsp.status_code == 401


def test_versions_post_permission_denied(
    client, user_without_organisation, user_codelist
):
    data = {"ecl": "<<128133004"}
    headers = {"HTTP_AUTHORIZATION": f"Token {user_without_organisation.api_token}"}

    with assert_no_difference(user_codelist.versions.count):
        rsp = client.post(user_codelist.get_versions_api_url(), data, **headers)

    assert rsp.status_code == 403
