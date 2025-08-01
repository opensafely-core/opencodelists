from django import template


register = template.Library()


@register.filter(name="truncatelines")
def truncatelines(value, max_lines=4):
    """
    Truncate a string to a maximum number of lines (split by newline).
    Usage: {{ field_to_truncate|truncatelines:4 }}
    """
    try:
        max_lines = int(max_lines)
    except Exception:
        max_lines = 4

    lines = str(value).splitlines()
    limited = "\n".join(lines[:max_lines])
    return limited
