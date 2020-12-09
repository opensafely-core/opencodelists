from django.contrib.auth import SESSION_KEY
from django.core.signing import Signer

from ...models import SET_PASSWORD_SALT
from ...views import user_set_password
from ..factories import UserFactory


def test_invalid_form(rf):
    user = UserFactory()

    data = {
        "new_password1": "test-test-test-1234",
        "new_password2": "",
    }
    request = rf.post("/", data=data)
    response = user_set_password(request, user.signed_username)

    assert response.status_code == 200

    assert response.context_data["form"].errors


def test_invalid_token(client):
    response = client.get("/users/activate/test/", follow=True)

    assert response.status_code == 200
    assert response.redirect_chain[0] == ("/", 302)

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Invalid User confirmation URL"


def test_renders_form(rf):
    user = UserFactory()

    request = rf.get("/")
    response = user_set_password(request, user.signed_username)

    assert response.status_code == 200
    assert "form" in response.context_data


def test_success(client):
    user = UserFactory()

    data = {
        "new_password1": "test-test-test-1234",
        "new_password2": "test-test-test-1234",
    }
    response = client.post(
        f"/users/activate/{user.signed_username}/", data=data, follow=True
    )

    assert response.status_code == 200

    # check user was logged in
    assert SESSION_KEY in client.session
    assert client.session[SESSION_KEY] == user.pk

    messages = list(response.context["messages"])
    assert len(messages) == 1
    expected = "You have successfully set your password and activated your account"
    assert str(messages[0]) == expected


def test_unknown_user(client):
    token = Signer(salt=SET_PASSWORD_SALT).sign("test")
    response = client.get(f"/users/activate/{token}/", follow=True)

    assert response.status_code == 200
    assert response.redirect_chain[0] == ("/", 302)
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Unknown User"
