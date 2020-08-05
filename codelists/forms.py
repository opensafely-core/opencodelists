from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from .models import Codelist, CodelistVersion, Reference, SignOff


class FormSetHelper(FormHelper):
    """
    FormHelper for use with Crispy Forms and FormSets

    When using Crispy Forms helpers with FormSet their layout is applied to the
    Forms but attributes to the FormSet, so we need to pass the FormHelper
    instance into the crispy_forms templatetag in the view.

    https://django-crispy-forms.readthedocs.io/en/latest/crispy_tag_formsets.html#formsets
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_csrf = True
        self.form_tag = False


class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        fields = [
            "text",
            "url",
        ]


class SignOffForm(forms.ModelForm):
    date = forms.DateField(widget=forms.TextInput(attrs={"type": "date"}))

    class Meta:
        model = SignOff
        fields = [
            "user",
            "date",
        ]


class CodelistForm(forms.ModelForm):
    csv_data = forms.FileField(label="CSV data")

    class Meta:
        model = Codelist
        fields = ["name", "coding_system_id", "description", "methodology", "csv_data"]

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        super().__init__(*args, **kwargs)


class CodelistVersionForm(forms.Form):
    csv_data = forms.FileField(label="CSV data")

    class Meta:
        model = CodelistVersion
        fields = ["csv_data"]

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))
        super().__init__(*args, **kwargs)
