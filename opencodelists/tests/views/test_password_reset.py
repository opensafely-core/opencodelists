import re
from urllib.parse import urlsplit

import pytest
from django.urls import reverse

from ...models import User


@pytest.mark.parametrize(
    "username", ["r3setuser", "res3t-user", "reset_us3r", "r3set-user_with-hyphen5"]
)
def test_password_reset_with_slug_username(client, mailoutbox, username):
    email_inbox = mailoutbox
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="hCSeKtZg",
        name="Reset User",
    )

    response = client.post(reverse("account_reset_password"), {"email": user.email})
    assert response.status_code == 302
    assert response.url == reverse("account_reset_password_done")
    assert len(email_inbox) == 1
    assert email_inbox[0].to == [user.email]
    reset_url = urlsplit(
        re.search(r"https?://[^\s]+", email_inbox[0].body).group()
    ).path

    # The token is stored in the session before displaying the password form.
    response = client.get(reset_url)
    assert response.status_code == 302
    form_url = response.url
    response = client.get(form_url)
    assert response.status_code == 200
    assert "token_fail" not in response.context
    assert b'name="password1"' in response.content

    response = client.post(form_url, {"password1": "hCSeKtZh", "password2": "hCSeKtZh"})
    assert response.status_code == 302
    assert response.url == reverse("account_reset_password_from_key_done")
    user.refresh_from_db()
    assert user.check_password("hCSeKtZh")
    assert not user.check_password("hCSeKtZg")

    # A successfully used token must not allow another password reset.
    response = client.get(reset_url)
    assert response.status_code == 200
    assert response.context["token_fail"]
    assert b"Invalid link" in response.content
