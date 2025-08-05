from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from codelists.forms import (
    CodelistUpdateForm,
    CSVValidationMixin,
    SignOffForm,
    methodology_template,
)
from coding_systems.versioning.models import CodingSystemRelease, ReleaseState
from opencodelists.models import User

from .helpers import csv_builder


def test_csvvalidation_byte_order_mark(bnf_data):
    form = CSVValidationMixin()

    # wrap CSV up in SimpleUploadedFile to mirror how a Django view would
    # handle it
    csv_data = "code,description\n0301012A0AA,Adrenaline (Asthma)"
    upload_file = csv_builder("\ufeff" + csv_data)
    uploaded_file = SimpleUploadedFile("our csv", upload_file.read())
    form.cleaned_data = {"csv_data": uploaded_file, "coding_system_id": "bnf"}
    assert form.clean_csv_data() == csv_data


def test_csvvalidation_correct_csv_column_count(bnf_data):
    form = CSVValidationMixin()

    # wrap CSV up in SimpleUploadedFile to mirror how a Django view would
    # handle it
    csv_data = "code,description\n0301012A0AA,Adrenaline (Asthma)"
    upload_file = csv_builder(csv_data)
    uploaded_file = SimpleUploadedFile("our csv", upload_file.read())
    form.cleaned_data = {"csv_data": uploaded_file, "coding_system_id": "bnf"}

    assert form.clean_csv_data() == csv_data


def test_csvvalidation_ignores_blank_lines(bnf_data):
    form = CSVValidationMixin()

    # Note extra newline inserted below
    csv_data = "code,description\n\n0301012A0AA,Adrenaline (Asthma)"
    upload_file = csv_builder(csv_data)
    uploaded_file = SimpleUploadedFile("our csv", upload_file.read())
    form.cleaned_data = {"csv_data": uploaded_file, "coding_system_id": "bnf"}

    assert form.clean_csv_data() == csv_data


def test_csvvalidation_coding_system_without_data():
    CodingSystemRelease.objects.create(
        release_name="unk",
        coding_system="opcs4",
        valid_from=date(2020, 1, 1),
        state=ReleaseState.READY,
    )
    # opcs4 has no coding system data, so we allow uploads without code validation
    form = CSVValidationMixin()

    # wrap CSV up in SimpleUploadedFile to mirror how a Django view would
    # handle it
    csv_data = "code,description\n0301012A0AA,Adrenaline (Asthma)"
    upload_file = csv_builder(csv_data)
    uploaded_file = SimpleUploadedFile("our csv", upload_file.read())
    form.cleaned_data = {"csv_data": uploaded_file, "coding_system_id": "opcs4"}

    assert form.clean_csv_data() == csv_data


def test_codelistform_incorrect_csv_column_count(bnf_data):
    form = CSVValidationMixin()

    # wrap CSV up in SimpleUploadedFile to mirror how a Django view would
    # handle it
    csv_data = "code,description\n0301012A0AA,Adrenaline (Asthma),test"
    upload_file = csv_builder(csv_data)
    uploaded_file = SimpleUploadedFile("our csv", upload_file.read())
    form.cleaned_data = {"csv_data": uploaded_file, "coding_system_id": "bnf"}

    with pytest.raises(ValidationError) as e:
        form.clean_csv_data()

    assert len(e.value.messages) == 1
    assert e.value.messages[0] == "Incorrect number of columns on row 1"


def test_codelistform_incorrect_header(bnf_data):
    form = CSVValidationMixin()

    # wrap CSV up in SimpleUploadedFile to mirror how a Django view would
    # handle it
    csv_data = "code ,description\n0301012A0AA,Adrenaline (Asthma)"
    upload_file = csv_builder(csv_data)
    uploaded_file = SimpleUploadedFile("our csv", upload_file.read())
    form.cleaned_data = {"csv_data": uploaded_file, "coding_system_id": "bnf"}

    with pytest.raises(ValidationError) as e:
        form.clean_csv_data()

    assert len(e.value.messages) == 1
    assert e.value.messages[0] == 'Header 1 ("code ") contains extraneous whitespace'


def test_codelistform_no_code_header(setup_coding_systems):
    form = CSVValidationMixin()

    # wrap CSV up in SimpleUploadedFile to mirror how a Django view would
    # handle it
    csv_data = "id,description\n0301012A0AA,Adrenaline (Asthma)"
    upload_file = csv_builder(csv_data)
    uploaded_file = SimpleUploadedFile("our csv", upload_file.read())
    form.cleaned_data = {"csv_data": uploaded_file, "coding_system_id": "bnf"}

    with pytest.raises(ValidationError) as e:
        form.clean_csv_data()

    assert len(e.value.messages) == 1
    assert (
        e.value.messages[0]
        == "Expected code header not found: 'dmd_id' or 'code' required"
    )


def test_codelistform_ambiguous_code_header(setup_coding_systems):
    form = CSVValidationMixin()

    # wrap CSV up in SimpleUploadedFile to mirror how a Django view would
    # handle it
    csv_data = "code,dmd_id,description\n0301012A0AA,0301012A0AA,Adrenaline (Asthma)"
    upload_file = csv_builder(csv_data)
    uploaded_file = SimpleUploadedFile("our csv", upload_file.read())
    form.cleaned_data = {"csv_data": uploaded_file, "coding_system_id": "bnf"}

    with pytest.raises(ValidationError) as e:
        form.clean_csv_data()

    assert len(e.value.messages) == 1
    assert e.value.messages[0] == "Ambiguous headers: both 'dmd_id' and 'code' found"


def test_codelistform_invalid_codes(setup_coding_systems):
    form = CSVValidationMixin()

    # wrap CSV up in SimpleUploadedFile to mirror how a Django view would
    # handle it
    csv_data = "code,description\n1234,Adrenaline (Asthma)"
    upload_file = csv_builder(csv_data)
    uploaded_file = SimpleUploadedFile("our csv", upload_file.read())
    form.cleaned_data = {"csv_data": uploaded_file, "coding_system_id": "bnf"}

    with pytest.raises(ValidationError) as e:
        form.clean_csv_data()

    assert len(e.value.messages) == 1
    assert e.value.messages[0] == (
        "CSV file contains 1 unknown code (1234) on line 1 "
        "(BNF release test, valid from 2020-01-01)"
    )


def test_signoff_form_ordered_by_username(
    organisation_admin,
    organisation_user,
    collaborator,
    user_without_organisation,
    user_with_no_api_token,
):
    # Usernames are:
    # organisation_admin: alice
    # organisation_user: bob
    # collaborator: charlie
    # user_without_organisation: dave
    # user_with_no_api_token: eve

    # Ordering of users in SignOffForm is by (case insensitive) username
    User.objects.create_user(
        username="Fred",
        password="test",
        email="fred@example.co.uk",
        name="Fred",
    )

    # ordering just by username puts title case names first
    assert list(
        User.objects.all().order_by("username").values_list("username", flat=True)
    ) == ["Fred", "alice", "bob", "charlie", "dave", "eve"]

    # the signoff form shows them in the model ordering (i.e. case insensitive)
    form = SignOffForm()
    user_field_choices = form.fields["user"].queryset
    assert list(user_field_choices.values_list("username", flat=True)) == [
        "alice",
        "bob",
        "charlie",
        "dave",
        "eve",
        "Fred",
    ]


def test_codelist_update_form_methodology_initial_values():
    """Test methodology field initial value behavior in different scenarios"""

    # (1) A new form has the methodology set to the template
    form1 = CodelistUpdateForm(owner_choices=[])
    assert form1.fields["methodology"].initial == methodology_template

    # (2) A form with methodology initial set to "" ends up with initial set to the template
    form2 = CodelistUpdateForm(owner_choices=[], initial={"methodology": ""})
    assert form2.initial["methodology"] == methodology_template

    # (3) A form with a non-blank methodology has that as the initial value
    custom_methodology = "This is a custom methodology that the user has written."
    form3 = CodelistUpdateForm(
        owner_choices=[], initial={"methodology": custom_methodology}
    )
    assert form3.initial["methodology"] == custom_methodology


def test_codelist_update_form_methodology_help_text():
    """Test that help text changes when methodology is not the template"""

    # Form with template methodology should have initial help text
    form1 = CodelistUpdateForm(owner_choices=[])
    initial_help_text = form1.fields["methodology"].help_text

    # Form with blank methodology should have the same initial help text
    form2 = CodelistUpdateForm(owner_choices=[], initial={"methodology": ""})
    assert form2.fields["methodology"].help_text == initial_help_text

    # Form with custom methodology should have different help text
    form3 = CodelistUpdateForm(
        owner_choices=[], initial={"methodology": "Non blank methodology"}
    )
    assert form3.fields["methodology"].help_text != initial_help_text

    # Form with unchanged template should have same help text
    form4 = CodelistUpdateForm(
        owner_choices=[], initial={"methodology": methodology_template}
    )
    assert form4.fields["methodology"].help_text == initial_help_text
