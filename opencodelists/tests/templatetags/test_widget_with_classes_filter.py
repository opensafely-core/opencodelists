from django import forms
from django.test import SimpleTestCase

from opencodelists.templatetags.widget_with_classes_filter import widget_with_classes


class DummyForm(forms.Form):
    name = forms.CharField()


class AddClassFilterTests(SimpleTestCase):
    def test_widget_with_classes(self):
        form = DummyForm()
        field = form["name"]

        # Apply the template filter
        rendered_widget = widget_with_classes(field, "custom-class")

        # Check if the class is added correctly
        self.assertIn('class=" custom-class"', str(rendered_widget))
