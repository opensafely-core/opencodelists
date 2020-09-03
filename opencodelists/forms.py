from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from .models import User


class UserForm(forms.ModelForm):
    class Meta:
        fields = [
            "username",
            "email",
            "name",
            "organisation",
        ]
        model = User

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))
        super().__init__(*args, **kwargs)
