import re

from django import template


register = template.Library()

# Reference: see `validate_slug` definition in Django source.
CLONED_CODELIST_NAME_PATTERN = re.compile(
    r"Cloned from codelist : \[(?P<name>[-a-zA-Z0-9_]+)\]"
)


@register.filter
def methodology_cloned_codelist_name_filter(methodology_text):
    """Template filter to escape methodology markdown formatting for cloned codelist names with underscore characters."""
    match = re.search(CLONED_CODELIST_NAME_PATTERN, methodology_text)
    if not match:
        return methodology_text

    escaped_name = match.group("name").replace("_", r"\_")
    return (
        methodology_text[: match.start("name")]
        + escaped_name
        + methodology_text[match.end("name") :]
    )
