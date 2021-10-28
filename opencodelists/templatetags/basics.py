from django import template

register = template.Library()


@register.filter
def getitem(dictionary, key):
    return dictionary[key]
