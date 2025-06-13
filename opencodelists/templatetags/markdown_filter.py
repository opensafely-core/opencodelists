import markdown2
import nh3
from django import template
from django.conf import settings


register = template.Library()


def _convert_markdown_to_html(text):
    """Internal function to convert markdown to HTML."""
    if not text:
        return ""
    text = markdown2.markdown(text)
    html = nh3.clean(
        text,
        tags=settings.MARKDOWN_FILTER_ALLOWLIST_TAGS,
        attributes=settings.MARKDOWN_FILTER_ALLOWLIST_ATTRIBUTES,
    )
    return html


@register.filter
def markdown_filter(text):
    """Template filter to convert markdown to safe HTML."""
    return _convert_markdown_to_html(text)


# Function to use in Python code
def render_markdown(text):
    """Direct function to convert markdown to HTML for use in Python code."""
    return _convert_markdown_to_html(text)
