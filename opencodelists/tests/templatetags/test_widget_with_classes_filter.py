from django import forms

from opencodelists.templatetags.widget_with_classes_filter import widget_with_classes


class DummyForm(forms.Form):
    name = forms.CharField()


def test_widget_with_classes():
    form = DummyForm()
    field = form["name"]

    # Apply the template filter
    rendered_widget = widget_with_classes(field, "custom-class")

    # Check if the class is added correctly
    assert 'class=" custom-class"' in str(rendered_widget)
