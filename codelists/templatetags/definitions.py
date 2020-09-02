from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def concept_url(coding_system_id, code):
    if coding_system_id == "ctv3tpp":
        coding_system_id = "ctv3"

    return reverse(f"{coding_system_id}:concept", args=[code])
