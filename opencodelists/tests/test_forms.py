import pytest
from django.core.exceptions import ValidationError

from ..forms import MembershipCreateForm, UserPasswordForm


def test_userpasswordform_different_passwords():
    form = UserPasswordForm()

    form.cleaned_data = {
        "new_password1": "test",
        "new_password2": "foo",
    }

    with pytest.raises(ValidationError) as e:
        form.clean_new_password2()

    assert len(e.value.messages) == 1
    assert e.value.messages[0] == "The two password fields don't match."


def test_membership_create_form(organisation, user_without_organisation):
    form = MembershipCreateForm(
        {"email": user_without_organisation.email}, organisation=organisation
    )
    assert form.is_valid()


def test_membership_create_form_already_member(organisation, organisation_user):
    form = MembershipCreateForm(
        {"email": organisation_user.email}, organisation=organisation
    )
    assert form.is_valid() is False
    assert form.errors == {
        "email": [
            f"User with email address {organisation_user.email} is already a member"
        ]
    }


def test_membership_create_form_no_user(organisation):
    form = MembershipCreateForm(
        {"email": "unknown@test.com"}, organisation=organisation
    )
    assert form.is_valid() is False
    assert form.errors == {
        "email": ["User with email address unknown@test.com does not exist"]
    }
