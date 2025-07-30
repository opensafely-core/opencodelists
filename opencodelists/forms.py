from django import forms
from django.contrib.auth import password_validation
from django.core.validators import RegexValidator

from codelists.coding_systems import builder_compatible_coding_systems
from codelists.models import Handle
from codelists.validation import CSVValidationMixin

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


def form_field_from_model(model_class, field_name, **kwargs):
    """Return a forms.Field instance derived from a models.Field,
    including the validators attached to the model field.

    Note:
    - `formfield` does not automatically inherit validators, as they may
      not always apply to a form field.
    - It is the caller's responsibility to ensure the validators are
      appropriate for their specific form."""
    model_field = model_class._meta.get_field(field_name)
    field_class = model_field.formfield
    validators = model_field.validators
    for validator in validators:
        if isinstance(validator, RegexValidator):
            kwargs["widget"] = forms.TextInput(
                attrs={
                    "pattern": f".*{validator.regex.pattern}.*",
                    "title": validator.message,
                }
            )
            break
    return field_class(validators=validators, **kwargs)


class CodelistCreateForm(forms.Form, CSVValidationMixin):
    owner = forms.ChoiceField()
    name = form_field_from_model(Handle, "name", label="Codelist name")
    coding_system_id = forms.ChoiceField(choices=[], label="Coding system")
    csv_data = forms.FileField(
        label="CSV data",
        required=False,
        help_text="The CSV file should not have a header, and its first column must contain valid codes in the chosen coding system.",
    )

    def __init__(self, *args, **kwargs):
        owner_choices = kwargs.pop("owner_choices")
        include_experimental = kwargs.pop("include_experimental")
        super().__init__(*args, **kwargs)
        coding_systems = [("", "---")] + [
            (
                system.id,
                system.name + " - EXPERIMENTAL PREVIEW"
                if system.is_experimental
                else system.name,
            )
            for system in builder_compatible_coding_systems(
                include_experimental=include_experimental
            )
        ]
        self.fields["coding_system_id"].choices = coding_systems

        if owner_choices:
            self.fields["owner"] = forms.ChoiceField(choices=owner_choices)
        else:
            del self.fields["owner"]

    def clean_csv_data(self):
        # check if any CSV data
        if not self.cleaned_data["csv_data"]:
            return

        # This upload path uses the codes from the CSV data.
        # We allow CSVs with headers or without,
        # and autodetect them.
        result = self.process_csv_data(allow_no_header=True)
        return result.codes


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


class MembershipCreateForm(forms.Form):
    user_idenitfier = forms.CharField(
        max_length=255,
        help_text="Enter a username or email address for an existing user",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username/Email"}
        ),
    )

    def __init__(self, *args, **kwargs):
        self.organisation = kwargs.pop("organisation")
        self.user = None
        super().__init__(*args, **kwargs)

        if "user_idenitfier" in self.errors:
            self.fields["user_idenitfier"].widget.attrs.update(
                {"class": "form-control border-danger"}
            )

    def clean_user_idenitfier(self):
        user_idenitfier = self.cleaned_data["user_idenitfier"]
        try:
            self.user = User.objects.get(username=user_idenitfier)
        except User.DoesNotExist:
            try:
                self.user = User.objects.get(email=user_idenitfier)
            except User.DoesNotExist:
                self.add_error(
                    "user_idenitfier", f"User {user_idenitfier} does not exist"
                )

        if self.user and self.user.is_member(self.organisation):
            self.add_error(
                "user_idenitfier", f"User {user_idenitfier} is already a member"
            )
        else:
            return user_idenitfier
