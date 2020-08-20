from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from .models import DraftCodelist


class DraftCodelistForm(forms.ModelForm):
    class Meta:
        model = DraftCodelist
        fields = ["name", "coding_system_id"]

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Create"))
        super().__init__(*args, **kwargs)
