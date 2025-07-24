from django import template
from ..models import EventDescriptors, TimeOfDay, EventLocationDescriptors

register = template.Library()

@register.filter
def event_descriptor_label(value):
    """
    Given an EventDescriptors Enum object, return its human readable label.
    """
    return EventDescriptors(value).label if value in EventDescriptors.values else value

@register.filter
def event_location_descriptor_label(value):
    """
    Given an EventLocationDescriptors Enum object, return its human readable label.
    """
    return EventLocationDescriptors(value).label if value in EventLocationDescriptors.values else value

@register.filter
def time_of_day_label(value):
    return TimeOfDay(value).label if value in TimeOfDay.values else value