from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def concept_url(coding_system_id, code):
    return reverse(f"{coding_system_id}:concept", args=[code])
