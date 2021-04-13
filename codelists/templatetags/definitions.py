from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def concept_url(coding_system_id, code):
    if coding_system_id == "bnf":
        # There's no BNF browser to link to at the moment
        return ""

    return reverse(f"{coding_system_id}:concept", args=[code])
