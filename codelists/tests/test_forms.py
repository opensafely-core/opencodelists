import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from codelists.forms import CSVValidationMixin

from .helpers import csv_builder


def test_csvvalidation_correct_csv_column_count():
    form = CSVValidationMixin()

    # wrap CSV up in SimpleUploadedFile to mirror how a Django view would
    # handle it
    csv_data = "code,description\n1067731000000107,Injury whilst swimming (disorder)"
    upload_file = csv_builder(csv_data)
    uploaded_file = SimpleUploadedFile("our csv", upload_file.read())
    form.cleaned_data = {"csv_data": uploaded_file}

    assert form.clean_csv_data() == csv_data


def test_codelistform_incorrect_csv_column_count():
    form = CSVValidationMixin()

    # wrap CSV up in SimpleUploadedFile to mirror how a Django view would
    # handle it
    csv_data = (
        "code,description\n1067731000000107,Injury whilst swimming (disorder),test"
    )
    upload_file = csv_builder(csv_data)
    uploaded_file = SimpleUploadedFile("our csv", upload_file.read())
    form.cleaned_data = {"csv_data": uploaded_file}

    with pytest.raises(ValidationError) as e:
        form.clean_csv_data()

    assert len(e.value.messages) == 1
    assert e.value.messages[0] == "Incorrect number of columns on row 1"
