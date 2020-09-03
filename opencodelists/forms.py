from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth import password_validation

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


class UserPasswordForm(forms.Form):
    """
    A form to let a user set their password without entering their old one.

    This is a reimplementation of Django's contrib.auth.forms.SetPasswordForm
    to not require a User object be passed in.
    """

    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")

        if password1 and password2:
            if password1 != password2:
                msg = "The two password fields don't match."
                raise forms.ValidationError(msg, code="password_mismatch")

        password_validation.validate_password(password2)

        return password2
