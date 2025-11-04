from django.test import SimpleTestCase
from core.templatetags.enum_tags import (
    event_descriptor_label,
    event_location_descriptor_label,
    time_of_day_label,
)
from core.models import EventDescriptors, EventLocationDescriptors, TimeOfDay

class TemplateTagsTests(SimpleTestCase):
    """
    Test class for the custom template tags.
    """

    def test_event_descriptor_label_with_valid_value(self):
        for choice in EventDescriptors.values:
            expected_label = EventDescriptors(choice).label
            self.assertEqual(event_descriptor_label(choice), expected_label)

    def test_event_descriptor_label_with_invalid_value(self):
        invalid_value = "INVALID_CHOICE"
        # For invalid value, filter returns value unchanged
        self.assertEqual(event_descriptor_label(invalid_value), invalid_value)

    def test_event_location_descriptor_label_with_valid_value(self):
        for choice in EventLocationDescriptors.values:
            expected_label = EventLocationDescriptors(choice).label
            self.assertEqual(event_location_descriptor_label(choice), expected_label)

    def test_event_location_descriptor_label_with_invalid_value(self):
        invalid_value = "INVALID_LOCATION"
        self.assertEqual(event_location_descriptor_label(invalid_value), invalid_value)

    def test_time_of_day_label_with_valid_value(self):
        for choice in TimeOfDay.values:
            expected_label = TimeOfDay(choice).label
            self.assertEqual(time_of_day_label(choice), expected_label)

    def test_time_of_day_label_with_invalid_value(self):
        invalid_value = "INVALID_TIME"
        self.assertEqual(time_of_day_label(invalid_value), invalid_value)
