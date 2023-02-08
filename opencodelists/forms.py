import csv
import operator
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

        # Eventually coding system version may be a selectable field, but for now it
        # just defaults to using the most recent one
        coding_system = CODING_SYSTEMS[
            self.cleaned_data["coding_system_id"]
        ].get_by_release_or_most_recent()

        data = f.read().decode("utf-8-sig")
        codes = [row[0] for row in csv.reader(StringIO(data))]
        validate_csv_data_codes(coding_system, codes)
        return codes


def validate_csv_data_codes(coding_system, codes):
    # Fully implemented codings systems have a `lookup_names` method that is used to
    # validate the codes in the CSV upload.  However, we also support uploads for some
    # coding systems that we don't maintain data for (e.g. OPCS4, ReadV2).  Skip code
    # validation for these systems, and just allow upload of the CSV data as it is.
    if not coding_system.has_database:
        return
    unknown_codes = set(codes) - set(coding_system.lookup_names(codes))
    unknown_codes_and_ixs = sorted(
        [(codes.index(code), code) for code in unknown_codes],
        key=operator.itemgetter(0),
    )

    if unknown_codes_and_ixs:
        line = unknown_codes_and_ixs[0][0] + 1
        code = unknown_codes_and_ixs[0][1]
        if len(unknown_codes_and_ixs) == 1:
            msg = f"CSV file contains 1 unknown code ({code}) on line {line}"
        else:
            num = len(unknown_codes_and_ixs)
            suffix = "" if num == 1 else "s"
            msg = f"CSV file contains {num} unknown code{suffix} -- the first ({code}) is on line {line}"
        msg += f" ({coding_system.short_name} release {coding_system.release_name}, valid from {coding_system.release.valid_from})"
        raise forms.ValidationError(msg)


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
