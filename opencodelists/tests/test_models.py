import pytest
from django.core.exceptions import ValidationError

from opencodelists.models import User


def test_is_member(organisation, organisation_user, user_without_organisation):
    assert organisation_user.is_member(organisation)
    assert not user_without_organisation.is_member(organisation)


def test_is_admin_member(
    organisation, organisation_admin, organisation_user, user_without_organisation
):
    assert organisation_admin.is_admin_member(organisation)
    assert not organisation_user.is_admin_member(organisation)
    assert not user_without_organisation.is_admin_member(organisation)


@pytest.mark.parametrize(
    "new_username,error",
    [
        ("bob", "A user with this username already exists"),
        ("Bob", "A user with this username already exists"),
        ("Bob@bob", "Enter a valid “slug”"),
    ],
)
def test_user_username_validation_on_create(organisation_user, new_username, error):
    assert organisation_user.username == "bob"
    with pytest.raises(ValidationError, match=error):
        User.objects.create_user(
            username=new_username,
            email="newbob@example.com",
            name="Bob1",
            password="test",
        )


def test_default_username_to_slugified_name():
    user = User.objects.create(
        email="bobuser@example.com", name="Bob User", password="test"
    )
    assert user.username == "bob-user"
