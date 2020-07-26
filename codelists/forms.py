from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from .models import Codelist


class CodelistForm(forms.ModelForm):
    csv_data = forms.FileField(label="CSV data")

    class Meta:
        model = Codelist
        fields = ["name", "coding_system_id", "description", "methodology", "csv_data"]

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))
        super().__init__(*args, **kwargs)


class CodelistVersionForm(forms.Form):
    pass
