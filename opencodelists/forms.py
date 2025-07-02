import csv
import operator
from io import StringIO

from django import forms
from django.contrib.auth import password_validation
from django.core.validators import RegexValidator

from codelists.coding_systems import CODING_SYSTEMS, builder_compatible_coding_systems
from codelists.models import Handle

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


class CodelistCreateForm(forms.Form):
    owner = forms.ChoiceField()
    name = form_field_from_model(Handle, "name", label="Codelist name")
    coding_system_id = forms.ChoiceField(choices=[], label="Coding system")
    csv_has_header = forms.TypedChoiceField(
        choices=(
            ("True", "Yes"),
            ("False", "No"),
        ),
        coerce=lambda x: x == "True",
        empty_value=None,
        widget=forms.RadioSelect,
        label="Does the CSV have a header row?",
        required=False,
    )
    csv_data = forms.FileField(
        label="CSV data",
        required=False,
        help_text="The CSV's first column must contain valid codes in the chosen coding system.",
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
        f = self.cleaned_data["csv_data"]
        if not f:
            return

        csv_has_header = self.cleaned_data["csv_has_header"]

        try:
            data = f.read().decode("utf-8-sig")
        except UnicodeDecodeError as exception:
            raise forms.ValidationError(
                "File could not be read. Please ensure the file contains CSV "
                "data (not Excel, for example). It should be a text file encoded "
                f"in the UTF-8 format. Error details: {exception}."
            )

        # Eventually coding system version may be a selectable field, but for now it
        # just defaults to using the most recent one.
        coding_system = CODING_SYSTEMS[
            self.cleaned_data["coding_system_id"]
        ].get_by_release_or_most_recent()

        csv_reader = csv.reader(StringIO(data))
        if csv_has_header:
            next(csv_reader, None)

        codes = [row[0] for row in csv_reader if row]

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
