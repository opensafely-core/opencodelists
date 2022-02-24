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
        {"user_idenitfier": user_without_organisation.email}, organisation=organisation
    )
    assert form.is_valid()

    form = MembershipCreateForm(
        {"user_idenitfier": user_without_organisation.username},
        organisation=organisation,
    )
    assert form.is_valid()


def test_membership_create_form_already_member(organisation, organisation_user):
    form = MembershipCreateForm(
        {"user_idenitfier": organisation_user.email}, organisation=organisation
    )
    assert form.is_valid() is False
    assert form.errors == {
        "user_idenitfier": [f"User {organisation_user.email} is already a member"]
    }


def test_membership_create_form_no_user(organisation):
    form = MembershipCreateForm(
        {"user_idenitfier": "unknown@test.com"}, organisation=organisation
    )
    assert form.is_valid() is False
    assert form.errors == {"user_idenitfier": ["User unknown@test.com does not exist"]}
