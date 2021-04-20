import json


def test_require_authentication_success(client, user, user_codelist):
    rsp = client.post(
        user_codelist.get_versions_api_url(),
        {"codes": ["128133004", "156659008"]},
        HTTP_AUTHORIZATION=f"Token {user.api_token}".encode("utf8"),
    )
    assert rsp.status_code == 200


def test_require_authentication_failure_no_header(client, user, user_codelist):
    # This tests that we return 401 when DRF's TokenAuthentication ignores a request
    # becuase no header is provided.

    rsp = client.post(user_codelist.get_versions_api_url())
    assert rsp.status_code == 401
    assert json.loads(rsp.content) == {
        "error": "Unauthenticated",
        "details": "No token header provided.",
    }


def test_require_authentication_failure_no_credentials(client, user, user_codelist):
    # This tests that we're using DRF's TokenAuthentication correctly.
    rsp = client.post(
        user_codelist.get_versions_api_url(),
        HTTP_AUTHORIZATION=b"Token",
    )
    assert rsp.status_code == 401
    assert json.loads(rsp.content) == {
        "error": "Unauthenticated",
        "details": "Invalid token header. No credentials provided.",
    }
