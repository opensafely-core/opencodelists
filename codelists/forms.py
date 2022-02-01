import csv
import re
from io import StringIO

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.forms.models import fields_for_model

from opencodelists.models import Organisation, User

from .models import Codelist, CodelistVersion, Handle, Reference, SignOff


def data_without_delete(cleaned_data):
    """
    Return data from this form without the DELETE key.

    When used with a formset_factory()'s can_delete kwarg a Form will gain
    a DELETE checkbox in the rendered <form>.  A FormSet uses this to know
    which submitted Forms have been deleted in the UI.

    However, we don't want that key when passing it to an action/the ORM.
    This function strips that key for us.
    """
    return {k: v for k, v in cleaned_data.items() if k != "DELETE"}


def model_field(model, fieldname):
    """Return a Field instance with arguments from the model definition."""

    return fields_for_model(model)[fieldname]


class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        fields = [
            "text",
            "url",
        ]


class BaseReferenceFormset(forms.BaseModelFormSet):
    def clean(self):
        """Checks that no two references have the same URL."""

        urls = [
            form.cleaned_data.get("url")
            for form in self.forms
            if not self._should_delete_form(form)
        ]

        if len(urls) != len(set(urls)):
            raise forms.ValidationError("References must have distinct URLs.")


ReferenceFormSet = forms.modelformset_factory(
    Reference, form=ReferenceForm, formset=BaseReferenceFormset, can_delete=True
)


class SignOffForm(forms.ModelForm):
    date = forms.DateField(widget=forms.TextInput(attrs={"type": "date"}))

    class Meta:
        model = SignOff
        fields = [
            "user",
            "date",
        ]


class BaseSignoffFormset(forms.BaseModelFormSet):
    def clean(self):
        """Checks that no two signoffs have the same user."""

        users = [
            form.cleaned_data.get("user")
            for form in self.forms
            if not self._should_delete_form(form)
        ]

        if len(users) != len(set(users)):
            raise forms.ValidationError("Signoffs must have distinct users.")


SignOffFormSet = forms.modelformset_factory(
    SignOff, form=SignOffForm, formset=BaseSignoffFormset, can_delete=True
)


class CSVValidationMixin:
    def clean_csv_data(self):
        data = self.cleaned_data["csv_data"].read().decode("utf-8-sig")

        reader = csv.reader(StringIO(data), quoting=csv.QUOTE_NONE)
        header = next(reader)  # expected to be headers
        num_columns = len(header)
        errors = [i for i, row in enumerate(reader) if len(row) != num_columns]

        if errors:
            msg = "Incorrect number of columns on row {}"
            raise forms.ValidationError(
                [
                    forms.ValidationError(msg.format(i + 1), code=f"row{i + 1}")
                    for i in errors
                ]
            )
        cleaned_header = [
            "".join(re.match(r"(\"?)\s*(\w+)\s*(\"?)", h).groups()) for h in header
        ]
        if header != cleaned_header:
            headersplit = data.split("\n", maxsplit=2)
            data = ",".join(cleaned_header) + "\n" + headersplit[1]

        return data


class CodelistCreateForm(forms.Form, CSVValidationMixin):
    name = model_field(Handle, "name")
    coding_system_id = model_field(Codelist, "coding_system_id")
    description = model_field(Codelist, "description")
    methodology = model_field(Codelist, "methodology")
    csv_data = forms.FileField(label="CSV data")

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        super().__init__(*args, **kwargs)


class CodelistUpdateForm(forms.Form):
    name = model_field(Handle, "name")
    slug = model_field(Handle, "slug")
    owner = forms.ChoiceField()  # The choices are set in __init__
    description = model_field(Codelist, "description")
    methodology = model_field(Codelist, "methodology")

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        owner_choices = kwargs.pop("owner_choices")
        super().__init__(*args, **kwargs)
        self.fields["owner"].choices = owner_choices

    def clean_owner(self):
        owner_identifier = self.cleaned_data["owner"]
        if owner_identifier.startswith("user:"):
            return User.objects.get(username=owner_identifier[5:])
        elif owner_identifier.startswith("organisation:"):
            return Organisation.objects.get(slug=owner_identifier[13:])
        else:
            assert False, owner_identifier


class CodelistVersionForm(forms.Form, CSVValidationMixin):
    csv_data = forms.FileField(label="CSV data")

    class Meta:
        model = CodelistVersion
        fields = ["csv_data"]

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))
        super().__init__(*args, **kwargs)
