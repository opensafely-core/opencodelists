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
    def _bind_form(self, file, **kwargs):
        return CodelistCreateForm(
            data={
                "name": "test name",
                "coding_system_id": "snomedct",
            }
            | kwargs,
            files={
                "csv_data": file,
            },
            owner_choices=[],
            include_experimental=False,
        )

    def test_bound_form_valid_with_no_csv_header(
        self, disorder_of_elbow_csv_data_no_header, disorder_of_elbow_codes
    ):
        file = ContentFile(disorder_of_elbow_csv_data_no_header.encode("utf-8"))
        file.name = "valid_data_no_header.csv"
        form = self._bind_form(file, csv_has_header="False")

        assert form.is_valid()
        assert form.cleaned_data["name"] == "test name"
        assert form.cleaned_data["coding_system_id"] == "snomedct"
        assert form.cleaned_data["csv_data"] == disorder_of_elbow_codes

    def test_bound_form_valid_with_csv_header(
        self, disorder_of_elbow_csv_data, disorder_of_elbow_codes
    ):
        file = ContentFile(disorder_of_elbow_csv_data.encode("utf-8"))
        file.name = "valid_data_with_header.csv"
        form = self._bind_form(file, csv_has_header="True")

        assert form.is_valid()
        assert form.cleaned_data["name"] == "test name"
        assert form.cleaned_data["coding_system_id"] == "snomedct"
        assert form.cleaned_data["csv_data"] == disorder_of_elbow_codes

    def test_bound_form_valid_header_not_specified_with_no_csv_header(
        self, disorder_of_elbow_csv_data_no_header, disorder_of_elbow_codes
    ):
        # We currently have the behaviour that if the user doesn't specify
        # whether the CSV has a header or not, we try processing as if it
        # doesn't have a header.
        file = ContentFile(disorder_of_elbow_csv_data_no_header.encode("utf-8"))
        file.name = "valid_data_no_header.csv"
        form = self._bind_form(file, csv_has_header=None)

        assert form.is_valid()
        assert form.cleaned_data["name"] == "test name"
        assert form.cleaned_data["coding_system_id"] == "snomedct"
        assert form.cleaned_data["csv_data"] == disorder_of_elbow_codes

    def test_bound_form_invalid_header_not_specified_with_csv_header(
        self, disorder_of_elbow_csv_data, disorder_of_elbow_codes
    ):
        # We currently have the behaviour that if the user doesn't specify
        # whether the CSV has a header or not, we try processing as if it
        # doesn't have a header.
        file = ContentFile(disorder_of_elbow_csv_data.encode("utf-8"))
        file.name = "valid_data_no_header.csv"
        form = self._bind_form(file, csv_has_header=None)

        assert not form.is_valid()
        errors = form.errors.get("csv_data")
        assert len(errors) == 1
        assert (
            "CSV file contains 1 unknown code (code) on line 1 (SNOMED CT release test, valid from 2020-01-01)"
            in errors[0]
        )

    def test_bound_form_invalid_file_unicode_error(self):
        invalid_utf8_data = b"\xff\xfe\xfd"
        file = ContentFile(invalid_utf8_data)
        file.name = "invalid_data.csv"
        form = self._bind_form(file, csv_has_header="False")

        assert not form.is_valid()
        errors = form.errors.get("csv_data")
        assert len(errors) == 1
        assert (
            "File could not be read. Please ensure the file contains CSV" in errors[0]
        )
