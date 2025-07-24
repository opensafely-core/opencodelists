from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from opencodelists.csv_utils import csv_data_to_rows
from opencodelists.forms import form_field_from_model, validate_csv_data_codes
from opencodelists.models import Organisation, User

from .models import Codelist, CodelistVersion, Handle, Reference, SignOff
from .validation import CSVValidationMixin


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


class CodelistCreateForm(forms.Form, CSVValidationMixin):
    name = form_field_from_model(Handle, "name")
    coding_system_id = form_field_from_model(Codelist, "coding_system_id")
    description = form_field_from_model(Codelist, "description")
    methodology = form_field_from_model(Codelist, "methodology")
    csv_data = forms.FileField(label="CSV data")

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        super().__init__(*args, **kwargs)

    def clean_csv_data(self):
        # This form can only use CSV data.
        decoded_csv_data = self.decode_csv()
        csv_rows = csv_data_to_rows(decoded_csv_data)

        coding_system = self.get_coding_system()

        code_col_ix = self.get_code_column_index(csv_rows[0], coding_system)

        # We currently enforce a header for CSVs uploaded with this form.
        codes = self.get_codes_from_header_csv(csv_rows, code_col_ix)

        validate_csv_data_codes(coding_system, codes)

        return self.cleaned_data["csv_data"]


class CodelistUpdateForm(forms.Form):
    name = form_field_from_model(Handle, "name")
    slug = form_field_from_model(Handle, "slug")
    owner = forms.ChoiceField()  # The choices are set in __init__
    description = form_field_from_model(Codelist, "description")
    methodology = form_field_from_model(Codelist, "methodology")

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
    coding_system_id = forms.CharField(widget=forms.HiddenInput())
    csv_data = forms.FileField(label="CSV data")

    class Meta:
        model = CodelistVersion
        fields = ["csv_data"]

    def __init__(self, *args, **kwargs):
        coding_system_id = kwargs.pop("coding_system_id", None)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))
        super().__init__(*args, **kwargs)
        self.fields["coding_system_id"].initial = coding_system_id
