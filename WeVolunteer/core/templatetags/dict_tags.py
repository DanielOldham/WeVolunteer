from django import template

register = template.Library()

@register.filter
def index_dict(d, key):
    """
    Given an object and a key, attempt to get the value at the key.
    Used for indexing dictionaries using dynamic keys in Django templates.
    """
    try:
        return d.get(key, None)
    except:
        return None
