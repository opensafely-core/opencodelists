import csv
from io import StringIO

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.utils.text import slugify

from .models import Codelist, CodelistVersion, Reference, SignOff


class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        fields = [
            "text",
            "url",
        ]


ReferenceFormSet = forms.modelformset_factory(
    Reference, form=ReferenceForm, can_delete=True
)


class SignOffForm(forms.ModelForm):
    date = forms.DateField(widget=forms.TextInput(attrs={"type": "date"}))

    class Meta:
        model = SignOff
        fields = [
            "user",
            "date",
        ]


SignOffFormSet = forms.modelformset_factory(SignOff, form=SignOffForm, can_delete=True)


class CodelistUniquenessMixin:
    def full_clean(self):
        """
        Override full_clean() to validate Name and Slug are unique to a Project.

        The Codelist forms don't include `project` or `slug` fields.  However,
        Codelists are unique based on the Project, Name, and Slug, and we still
        want to take advantage of Django's ModelForm validation handling so we
        can report non-unique errors to the user.

        This method calls ModelForm's full_clean() to copy values from the form
        to the instance.  Both the Create and Update views pass in an instance
        (either with just a Project or with the existing Codelist which also
        has it's Project).  It then generates a Slug before validating
        uniqueness of the instance and adding errors if appropriate.
        """
        # Call super()'s full_clean to populate the Codelist instance with
        # values from the form.
        super().full_clean()

        # populate the instance's slug so the validate_unique() check below can
        # use it to check uniqueness
        self.instance.slug = slugify(self.instance.name)

        # Validate uniqueness of the instance now it's been populated with
        # values from the form and the Project instance.
        #
        # We call this manually, rather than using BaseModelForm's
        # validate_unique() because that makes a call to
        # _get_validation_exclusions() to build up a list of a excluded fields.
        # This removes fields not defined on the form (among other things)
        # which drops our slug field.
        try:
            self.instance.validate_unique()
        except forms.ValidationError as e:
            self.add_error(None, e)


class CSVValidationMixin:
    def clean_csv_data(self):
        data = self.cleaned_data["csv_data"].read().decode("utf-8-sig")

        reader = csv.reader(StringIO(data))
        num_columns = len(next(reader))  # expected to be headers
        errors = [i for i, row in enumerate(reader) if len(row) != num_columns]

        if errors:
            msg = "Incorrect number of columns on row {}"
            raise forms.ValidationError(
                [
                    forms.ValidationError(msg.format(i + 1), code=f"row{i + 1}")
                    for i in errors
                ]
            )

        return data


class CodelistCreateForm(CodelistUniquenessMixin, forms.ModelForm, CSVValidationMixin):
    csv_data = forms.FileField(label="CSV data")

    class Meta:
        model = Codelist
        fields = ["name", "coding_system_id", "description", "methodology", "csv_data"]

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        super().__init__(*args, **kwargs)


class CodelistUpdateForm(CodelistUniquenessMixin, forms.ModelForm):
    class Meta:
        fields = [
            "name",
            "project",
            "coding_system_id",
            "description",
            "methodology",
        ]
        model = Codelist

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        super().__init__(*args, **kwargs)


class CodelistVersionForm(forms.Form, CSVValidationMixin):
    csv_data = forms.FileField(label="CSV data")

    class Meta:
        model = CodelistVersion
        fields = ["csv_data"]

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))
        super().__init__(*args, **kwargs)
