import pytest

from ..models import User
from ..views import UserCreate
from .factories import OrganisationFactory, UserFactory

pytestmark = [
    pytest.mark.filterwarnings(
        "ignore::DeprecationWarning:bleach",
        "ignore::django.utils.deprecation.RemovedInDjango40Warning:debug_toolbar",
    ),
]


def test_usercreate_renders_form(rf):
    request = rf.get("/")
    request.user = UserFactory()

    response = UserCreate.as_view()(request)

    assert response.status_code == 200


def test_usercreate_creates_user(client):
    org = OrganisationFactory(slug="datalab")
    data = {
        "username": "new-user",
        "name": "New User",
        "email": "new@example.com",
        "organisation": "datalab",
    }

    client.force_login(UserFactory())
    response = client.post("/users/add/", data=data)

    assert response.status_code == 302

    user = User.objects.first()
    assert user.username == "new-user"
    assert user.name == "New User"
    assert user.email == "new@example.com"
    assert user.organisation == org
