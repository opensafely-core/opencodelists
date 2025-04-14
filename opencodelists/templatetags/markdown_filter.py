import markdown2
import nh3
from django import template
from django.conf import settings


register = template.Library()


@register.filter
def markdown_filter(text):
    text = markdown2.markdown(text)
    html = nh3.clean(
        text,
        tags=settings.MARKDOWN_FILTER_ALLOWLIST_TAGS,
        attributes=settings.MARKDOWN_FILTER_ALLOWLIST_ATTRIBUTES,
        css_sanitizer=settings.MARKDOWN_FILTER_ALLOWLIST_STYLES,
    )
    return html
