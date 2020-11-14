import pytest
from django.contrib.auth import SESSION_KEY
from django.core.signing import Signer

from ..models import SET_PASSWORD_SALT, User
from ..views import UserCreate, user_set_password
from .factories import UserFactory

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore::DeprecationWarning:bleach",
        "ignore::django.utils.deprecation.RemovedInDjango40Warning:debug_toolbar",
    ),
]


def test_useractivationurl_already_active(client):
    user = UserFactory(is_active=True)

    client.force_login(UserFactory())
    response = client.get(f"/users/added/{user.username}/", follow=True)

    assert response.status_code == 200

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == f"User '{user.username}' has already been activated."


def test_useractivationurl_success(client):
    user = UserFactory(is_active=False)

    client.force_login(UserFactory())
    response = client.get(f"/users/added/{user.username}/")

    assert response.status_code == 200

    messages = list(response.context["messages"])
    assert len(messages) == 0


def test_useractivationurl_unknown_user(client):
    client.force_login(UserFactory())
    response = client.get("/users/added/foo/", follow=True)

    assert response.status_code == 200

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Unknown user 'foo'"


def test_usercreate_renders_form(rf):
    request = rf.get("/")
    request.user = UserFactory()

    response = UserCreate.as_view()(request)

    assert response.status_code == 200


def test_usercreate_creates_user(client):
    data = {
        "username": "new-user",
        "name": "New User",
        "email": "new@example.com",
    }

    client.force_login(UserFactory())
    response = client.post("/users/add/", data=data)

    assert response.status_code == 302

    user = User.objects.first()
    assert user.username == "new-user"
    assert user.name == "New User"
    assert user.email == "new@example.com"


def test_usersetpassword_invalid_form(rf):
    user = UserFactory()

    data = {
        "new_password1": "test-test-test-1234",
        "new_password2": "",
    }
    request = rf.post("/", data=data)
    response = user_set_password(request, user.signed_username)

    assert response.status_code == 200

    assert response.context_data["form"].errors


def test_usersetpassword_invalid_token(client):
    response = client.get("/users/activate/test/", follow=True)

    assert response.status_code == 200
    assert response.redirect_chain[0] == ("/", 302)

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Invalid User confirmation URL"


def test_usersetpassword_renders_form(rf):
    user = UserFactory()

    request = rf.get("/")
    response = user_set_password(request, user.signed_username)

    assert response.status_code == 200
    assert "form" in response.context_data


def test_usersetpassword_success(client):
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


def test_usersetpassword_unknown_user(client):
    token = Signer(salt=SET_PASSWORD_SALT).sign("test")
    response = client.get(f"/users/activate/{token}/", follow=True)

    assert response.status_code == 200
    assert response.redirect_chain[0] == ("/", 302)
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Unknown User"
