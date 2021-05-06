def test_already_active(client, user, organisation_admin):
    client.force_login(organisation_admin)
    response = client.get(f"/users/added/{user.username}/", follow=True)

    assert response.status_code == 200

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == f"User '{user.username}' has already been activated."


def test_success(client, inactive_user, organisation_admin):
    client.force_login(organisation_admin)
    response = client.get(f"/users/added/{inactive_user.username}/")

    assert response.status_code == 200

    messages = list(response.context["messages"])
    assert len(messages) == 0


def test_unknown_user(client, organisation_admin):
    client.force_login(organisation_admin)
    response = client.get("/users/added/foo/", follow=True)

    assert response.status_code == 200

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Unknown user 'foo'"
