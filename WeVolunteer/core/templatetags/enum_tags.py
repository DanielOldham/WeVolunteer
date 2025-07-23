from django import template
from ..models import EventDescriptorTags, TimeOfDay

register = template.Library()

@register.filter
def event_descriptor_label(value):
    """
    Given an EventDescriptorTags Enum object, return its human readable label.
    """
    return EventDescriptorTags(value).label if value in EventDescriptorTags.values else value

@register.filter
def time_of_day_label(value):
    return TimeOfDay(value).label if value in TimeOfDay.values else value