from unittest.mock import patch

from django.forms import ValidationError

from ...models import User
from ..assertions import assert_difference, assert_no_difference


def test_get(client):
    rsp = client.get("/accounts/register/")
    assert rsp.status_code == 200


def test_get_when_authenticated(client, user):
    client.force_login(user)
    rsp = client.get("/accounts/register/")
    assert rsp.status_code == 302


def test_post_success(client):
    assert not User.objects.filter(username="user").exists()

    data = {
        "username": "user",
        "name": "Prof User",
        "email": "user@example.com",
        "password1": "hCSeKtZg",
        "password2": "hCSeKtZg",
    }

    with assert_difference(User.objects.count, expected_difference=1):
        client.post("/accounts/register/", data)

    u = User.objects.get(username="user")
    assert u.name == "Prof User"
    assert u.email == "user@example.com"
    assert u.check_password("hCSeKtZg")
    assert u.is_active
    assert not u.is_staff


def test_post_failure_pasword_mismatch(client):
    data = {
        "username": "user",
        "name": "Prof User",
        "email": "user@example.com",
        "password1": "password",
        "password2": "wordpass",
    }

    with assert_no_difference(User.objects.count):
        rsp = client.post("/accounts/register/", data)

    assert b"The two password fields didn&#x27;t match." in rsp.content


def test_post_failure_duplicate_username(client, user):
    data = {
        "username": user.username,
        "name": "Prof User",
        "email": "user@example.com",
        "password1": "password",
        "password2": "wordpass",
    }

    with assert_no_difference(User.objects.count):
        rsp = client.post("/accounts/register/", data)

    assert b"A user with this username already exists." in rsp.content


def test_post_failure_duplicate_email(client, user):
    data = {
        "username": "user",
        "name": "Prof User",
        "email": user.email,
        "password1": "password",
        "password2": "wordpass",
    }

    with assert_no_difference(User.objects.count):
        rsp = client.post("/accounts/register/", data)

    assert b"A user with this email address already exists." in rsp.content


def test_post_failure_duplicate_username_unhandled(client, user):
    # We had an odd sentry error whereby a duplicate username caused a
    # ValidationError to be raised. This shouldn't happend because the form
    # should catch this in the call to is_valid() and return an error to the user
    # instead of raising an unhandled exception.
    # This test is to ensure that if this happens again, we handle it gracefully.
    data = {
        "username": "new-one",
        "name": "Prof User",
        "email": "user@example.com",
        "password1": "hCSeKtZg",
        "password2": "hCSeKtZg",
    }

    with (
        patch(
            "opencodelists.models.User.save",
            side_effect=ValidationError("A user with this username already exists."),
        ),
    ):
        with assert_no_difference(User.objects.count):
            rsp = client.post("/accounts/register/", data)

    assert b"A user with this username already exists." in rsp.content
