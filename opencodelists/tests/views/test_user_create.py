from ...models import User
from ...views import UserCreate
from ..factories import UserFactory


def test_renders_form(rf):
    request = rf.get("/")
    request.user = UserFactory()

    response = UserCreate.as_view()(request)

    assert response.status_code == 200


def test_creates_user(client):
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
