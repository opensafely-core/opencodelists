import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from ..forms import CodelistCreateForm, MembershipCreateForm, UserPasswordForm


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


class TestCodelistCreateForm:
    def _bind_form(self, file):
        return CodelistCreateForm(
            data={
                "name": "test name",
                "coding_system_id": "snomedct",
            },
            files={
                "csv_data": file,
            },
            owner_choices=[],
        )

    def test_bound_form_valid(self, disorder_of_elbow_codes):
        valid_csv_data = "\n".join(disorder_of_elbow_codes)
        file = ContentFile(valid_csv_data.encode("utf-8"))
        file.name = "valid_data.csv"
        form = self._bind_form(file)

        assert form.is_valid()
        assert form.cleaned_data["name"] == "test name"
        assert form.cleaned_data["coding_system_id"] == "snomedct"
        assert form.cleaned_data["csv_data"] == disorder_of_elbow_codes

    def test_bound_form_invalid_file_unicode_error(self):
        invalid_utf8_data = b"\xff\xfe\xfd"
        file = ContentFile(invalid_utf8_data)
        file.name = "invalid_data.csv"
        form = self._bind_form(file)

        assert not form.is_valid()
        errors = form.errors.get("csv_data")
        len(errors) == 1
        assert (
            "File could not be read. Please ensure the file contains CSV" in errors[0]
        )
