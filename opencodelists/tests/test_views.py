from django.contrib.auth import SESSION_KEY
from django.core.signing import Signer

from codelists.tests.helpers import csv_builder

from ..models import SET_PASSWORD_SALT, User
from ..views import UserCreate, user_set_password
from .assertions import assert_difference, assert_no_difference
from .factories import UserFactory


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
    assert not User.objects.filter(username="new-user").exists()

    data = {
        "username": "new-user",
        "name": "New User",
        "email": "new@example.com",
    }

    client.force_login(UserFactory())
    response = client.post("/users/add/", data=data)

    assert response.status_code == 302

    user = User.objects.get(username="new-user")
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


def test_user_create_codelist_get(client):
    user = UserFactory()
    client.force_login(user)

    response = client.get(f"/users/{user.username}/new-codelist/")

    assert response.status_code == 200


def test_user_create_codelist_post_valid_with_csv(client, tennis_elbow):
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


def test_user_create_codelist_post_invalid_with_csv(client, tennis_elbow):
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


def test_user_create_codelist_post_valid_without_csv(client):
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


def test_user_create_codelist_post_duplicate_name(client):
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


def test_register_get(client):
    rsp = client.get("/accounts/register/")
    assert rsp.status_code == 200


def test_register_get_when_authenticated(client):
    user = UserFactory()
    client.force_login(user)
    rsp = client.get("/accounts/register/")
    assert rsp.status_code == 302


def test_register_post_success(client):
    assert not User.objects.filter(username="user").exists()

    data = {
        "username": "user",
        "name": "Prof User",
        "email": "user@example.com",
        "password1": "password",
        "password2": "password",
    }

    with assert_difference(User.objects.count, expected_difference=1):
        client.post("/accounts/register/", data)

    u = User.objects.get(username="user")
    assert u.name == "Prof User"
    assert u.email == "user@example.com"
    assert u.check_password("password")
    assert u.is_active
    assert not u.is_staff


def test_register_post_failure_pasword_mismatch(client):
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


def test_register_post_failure_duplicate_username(client):
    u = UserFactory()

    data = {
        "username": u.username,
        "name": "Prof User",
        "email": "user@example.com",
        "password1": "password",
        "password2": "wordpass",
    }

    with assert_no_difference(User.objects.count):
        rsp = client.post("/accounts/register/", data)

    assert b"A user with this username already exists." in rsp.content


def test_register_post_failure_duplicate_email(client):
    u = UserFactory()

    data = {
        "username": "user",
        "name": "Prof User",
        "email": u.email,
        "password1": "password",
        "password2": "wordpass",
    }

    with assert_no_difference(User.objects.count):
        rsp = client.post("/accounts/register/", data)

    assert b"A user with this email address already exists." in rsp.content
