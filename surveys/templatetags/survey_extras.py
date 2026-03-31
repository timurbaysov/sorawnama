from django import template

register = template.Library()


@register.filter
def dict_get(d, key):
    """Get a value from a dictionary by key. Usage: {{ mydict|dict_get:key }}"""
    if isinstance(d, dict):
        return d.get(key)
    return None
