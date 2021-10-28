from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def include_exclude_button(symbol, status):
    if status == symbol:
        button_class = "btn-primary"
    elif status == f"({symbol})":
        button_class = "btn-secondary"
    else:
        button_class = "btn-outline-secondary"

    return format_html(
        '<button type="button" class="btn {} py-0">{}</button>', button_class, symbol
    )
