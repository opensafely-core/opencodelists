import csv
from io import StringIO

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from opencodelists.forms import form_field_from_model, validate_csv_data_codes
from opencodelists.models import Organisation, User

from .coding_systems import CODING_SYSTEMS
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
        # Eventually coding system version may be a selectable field, but for now it
        # just defaults to using the most recent one
        coding_system = CODING_SYSTEMS[
            self.cleaned_data["coding_system_id"]
        ].get_by_release_or_most_recent()

        data = self.cleaned_data["csv_data"].read().decode("utf-8-sig")

        reader = csv.reader(StringIO(data))
        header = next(reader)  # expected to be headers

        for i, value in enumerate(header):
            if value != value.strip():
                raise forms.ValidationError(
                    f'Header {i + 1} ("{value}") contains extraneous whitespace'
                )

        # restrict the headers we expect
        # BNF codelists downloaded as dm+d will have a `dmd_id` column that contains the
        # code; for all others, expect a `code` column.
        possible_code_headers = {"dmd_id", "code"}
        code_headers = possible_code_headers & set(header)
        if not code_headers:
            raise forms.ValidationError(
                "Expected code header not found: 'dmd_id' or 'code' required"
            )
        if code_headers == possible_code_headers:
            raise forms.ValidationError(
                "Ambiguous headers: both 'dmd_id' and 'code' found"
            )

        code_header = next(col for col in possible_code_headers if col in header)
        code_col_ix = header.index(code_header)
        num_columns = len(header)

        number_of_column_errors = []
        codes = []
        for i, row in enumerate(reader, start=1):
            # Ignore completely blank lines
            if not row:
                continue
            if len(row) != num_columns:
                number_of_column_errors.append(i)
            codes.append(row[code_col_ix])

        if number_of_column_errors:
            msg = "Incorrect number of columns on row {}"
            raise forms.ValidationError(
                [
                    forms.ValidationError(msg.format(i), code=f"row{i}")
                    for i in number_of_column_errors
                ]
            )

        validate_csv_data_codes(coding_system, codes)
        return data


description_max_length = 500
description_help_text = (
    f"This is the short summary (max {description_max_length} characters) that "
    "will be shown with search results. E.g."
    "<ul>"
    '<li>This codelist contains all codes referred to in the "has_dementia" field of the QCovid assessment tool.</li>'
    "<li>This codelist aims to identify SSRIs that are more likely to be prescribed in obsessive compulsive disorder</li>"
    "</ul>"
)
methodology_help_text = (
    "<p>A longer description of how the codelist was created, its intended use, and any "
    "relevant background information. It will be shown on the codelist page and help users understand "
    "the codelist's purpose and context. This field supports "
    "<a href='https://www.markdownguide.org/basic-syntax/' target='_blank' rel='noopener noreferrer'>markdown formatting</a>.</p>"
)
methodology_initial_help_text = methodology_help_text + (
    "<p>The above is a markdown template with a suggested structure for your metadata. "
    "We recommend keeping the subheadings, and replacing the text beneath each one. These "
    "subheadings are generally seen as useful things to capture, but don't always apply, so "
    "feel free to delete as appropriate, or add additional ones.</p>"
)
methodology_template = (
    "# Context\n\n"
    "Is this for a specific purpose or context, if so what, or could it be used more broadly?\n\n"
    "# Inclusion/exclusion criteria\n\n"
    "Describe the inclusion and exclusion criteria used to define the codelist.\n\n"
    "# Borderline cases\n\n"
    "List any codes which were considered borderline, and explain why they were included/excluded.\n\n"
    "# Sensitivity vs specificity\n\n"
    "Is the aim of this codelist to be specific (e.g. hypertension via confirmed diagnosis codes), "
    "or sensitive (e.g. flu via potential symptom codes)?\n\n"
    "# Additional information\n\n"
    "Any other relevant information about the codelist."
)


class CodelistCreateForm(forms.Form, CSVValidationMixin):
    name = form_field_from_model(Handle, "name")
    coding_system_id = form_field_from_model(Codelist, "coding_system_id")
    description = form_field_from_model(
        Codelist,
        "description",
        help_text=description_help_text,
        widget=forms.Textarea(attrs={"maxlength": description_max_length}),
    )
    methodology = form_field_from_model(
        Codelist,
        "methodology",
        help_text=methodology_initial_help_text,
        initial=methodology_template,
    )
    csv_data = forms.FileField(label="CSV data")

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        super().__init__(*args, **kwargs)


class CodelistUpdateForm(forms.Form):
    name = form_field_from_model(Handle, "name")
    slug = form_field_from_model(Handle, "slug")
    owner = forms.ChoiceField()  # The choices are set in __init__
    description = form_field_from_model(
        Codelist,
        "description",
        help_text=description_help_text,
        widget=forms.Textarea(attrs={"maxlength": description_max_length}),
    )
    methodology = form_field_from_model(
        Codelist,
        "methodology",
        help_text=methodology_initial_help_text,
        initial=methodology_template,
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        owner_choices = kwargs.pop("owner_choices")
        super().__init__(*args, **kwargs)
        self.fields["owner"].choices = owner_choices

        # If this form is not bound (i.e., no POST data)
        if not self.is_bound:
            # Remove maxlength if initial description is too long so that
            # we can support old descriptions that exceed the limit.
            desc_field = self.fields["description"]
            initial_desc = self.initial.get("description")
            if initial_desc:
                normalized_desc = initial_desc.replace("\r\n", "\n").replace("\r", "\n")
                if len(normalized_desc) > description_max_length:
                    desc_field.widget.attrs.pop("maxlength", None)

            # If the methodology is not set, use the template
            methodology_initial = self.initial.get("methodology", "")
            if methodology_initial == "":
                self.initial["methodology"] = methodology_template

            # Change the help text if the methodology is not the template i.e. edited by the user
            if methodology_initial:
                normalized_methodology = methodology_initial.replace(
                    "\r\n", "\n"
                ).replace("\r", "\n")
                if normalized_methodology != methodology_template:
                    self.fields["methodology"].help_text = methodology_help_text

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
