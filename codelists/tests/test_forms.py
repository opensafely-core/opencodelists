import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from codelists.forms import CSVValidationMixin

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


def test_codelistform_no_code_header():
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


def test_codelistform_ambiguous_code_header():
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


def test_codelistform_invalid_codes():
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
