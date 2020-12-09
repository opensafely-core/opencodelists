from ..factories import UserFactory


def test_already_active(client):
    user = UserFactory(is_active=True)

    client.force_login(UserFactory())
    response = client.get(f"/users/added/{user.username}/", follow=True)

    assert response.status_code == 200

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == f"User '{user.username}' has already been activated."


def test_success(client):
    user = UserFactory(is_active=False)

    client.force_login(UserFactory())
    response = client.get(f"/users/added/{user.username}/")

    assert response.status_code == 200

    messages = list(response.context["messages"])
    assert len(messages) == 0


def test_unknown_user(client):
    client.force_login(UserFactory())
    response = client.get("/users/added/foo/", follow=True)

    assert response.status_code == 200

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Unknown user 'foo'"
