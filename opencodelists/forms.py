import csv
from io import StringIO

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth import password_validation

from codelists.coding_systems import CODING_SYSTEMS

from .models import User


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


class CodelistCreateForm(forms.Form):
    CODING_SYSTEM_CHOICES = [("", "---")] + sorted(
        (id, system.name)
        for id, system in CODING_SYSTEMS.items()
        if hasattr(system, "ancestor_relationships")
    )

    owner = forms.ChoiceField()
    name = forms.CharField(max_length=255, label="Codelist name")
    coding_system_id = forms.ChoiceField(
        choices=CODING_SYSTEM_CHOICES, label="Coding system"
    )
    csv_data = forms.FileField(
        label="CSV data",
        required=False,
        help_text="Optional.  If provided, the CSV file should not have a header, and its first column must contain valid codes in the chosen coding system.",
    )

    def __init__(self, *args, **kwargs):
        owner_choices = kwargs.pop("owner_choices")
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Create"))
        super().__init__(*args, **kwargs)
        if owner_choices:
            self.fields["owner"] = forms.ChoiceField(choices=owner_choices)
        else:
            del self.fields["owner"]

    def clean_csv_data(self):
        f = self.cleaned_data["csv_data"]
        if not f:
            return

        coding_system = CODING_SYSTEMS[self.cleaned_data["coding_system_id"]]

        data = f.read().decode("utf-8-sig")
        codes = [row[0] for row in csv.reader(StringIO(data))]
        code_to_term = coding_system.code_to_term(codes)
        unknown_codes_and_ixs = [
            (ix, code) for ix, code in enumerate(codes) if code not in code_to_term
        ]

        if unknown_codes_and_ixs:
            line = unknown_codes_and_ixs[0][0] + 1
            code = unknown_codes_and_ixs[0][1]
            if len(unknown_codes_and_ixs) == 1:
                msg = f"CSV file contains 1 unknown code ({code}) on line {line}"
            else:
                num = len(unknown_codes_and_ixs)
                msg = f"CSV file contains {num} unknown code -- the first ({code}) is on line {line}"
            raise forms.ValidationError(msg)

        return codes


class RegisterForm(forms.ModelForm):
    """Form for users to register.

    We cannot use UserCreationForm because our custom User model is not a subclass of
    AbstractUser.
    """

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput,
        strip=False,
        help_text="Enter the same password as before, for verification.",
    )

    error_messages = {
        "password_mismatch": "The two password fields didn't match.",
    }

    class Meta:
        model = User
        fields = ["username", "name", "email", "password1", "password2"]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        self.instance.username = self.cleaned_data.get("username")
        password_validation.validate_password(
            self.cleaned_data.get("password2"), self.instance
        )
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
