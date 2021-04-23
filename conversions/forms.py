from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from codelists.coding_systems import CODING_SYSTEMS


class ConvertForm(forms.Form):
    CODING_SYSTEMS_CHOICES = [
        ("", ""),
        ("snomedct", CODING_SYSTEMS["snomedct"].name),
        ("ctv3", CODING_SYSTEMS["ctv3"].name),
    ]
    TYPE_CHOICES = [
        ("full", "Download full mapping"),
        ("to-codes-only", "Only include converted concepts"),
    ]

    from_coding_system_id = forms.ChoiceField(
        choices=CODING_SYSTEMS_CHOICES, label="Convert from"
    )
    to_coding_system_id = forms.ChoiceField(
        choices=CODING_SYSTEMS_CHOICES, label="Convert to"
    )
    csv_data = forms.FileField(
        label="CSV data",
        help_text="The CSV file should not have a header, and its first column must contain valid codes in the chosen coding system.",
    )
    type = forms.ChoiceField(choices=TYPE_CHOICES)
    include_unassured = forms.BooleanField(
        label="Include mappings that have not been assured", required=False
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))
        super().__init__(*args, **kwargs)

    def clean_to_coding_system_id(self):
        to_coding_system_id = self.cleaned_data.get("to_coding_system_id")
        from_coding_system_id = self.cleaned_data.get("from_coding_system_id")

        if to_coding_system_id == from_coding_system_id:
            raise forms.ValidationError("Coding systems should not match")

        return to_coding_system_id
