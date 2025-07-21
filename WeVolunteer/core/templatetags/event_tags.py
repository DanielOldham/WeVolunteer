from django import template
from ..models import EventDescriptorTags

register = template.Library()

@register.filter
def event_descriptor_label(value):
    """
    Given an EventDescriptorTags Enum object, return its human readable label.
    """
    return EventDescriptorTags(value).label if value in EventDescriptorTags.values else value
