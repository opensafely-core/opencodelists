from django import forms

from .models import ADDITIONAL_RELATIONSHIP, INFERRED_RELATIONSHIP, STATED_RELATIONSHIP


class BrowserForm(forms.Form):
    RELATIONSHIP_CHIOCES = [
        (STATED_RELATIONSHIP, "stated"),
        (INFERRED_RELATIONSHIP, "inferred"),
        (ADDITIONAL_RELATIONSHIP, "additional"),
    ]

    relationship_types = forms.MultipleChoiceField(
        choices=RELATIONSHIP_CHIOCES, required=True
    )
