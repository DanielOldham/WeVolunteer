from django.test import SimpleTestCase
from core.templatetags.enum_tags import (
    event_descriptor_label,
    event_location_descriptor_label,
    time_of_day_label,
)
from core.templatetags.dict_tags import index_dict
from core.models import EventDescriptors, EventLocationDescriptors, TimeOfDay

class EnumTagsTests(SimpleTestCase):
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


class DictTagsTests(SimpleTestCase):
    def test_index_dict_with_valid_key(self):
        sample_dict = {"a": 1, "b": 2}
        self.assertEqual(index_dict(sample_dict, "a"), 1)
        self.assertEqual(index_dict(sample_dict, "b"), 2)

    def test_index_dict_with_missing_key(self):
        sample_dict = {"a": 1}
        self.assertIsNone(index_dict(sample_dict, "missing"))

    def test_index_dict_with_none_dict(self):
        self.assertIsNone(index_dict(None, "anykey"))

    def test_index_dict_with_non_dict_input(self):
        self.assertIsNone(index_dict("string", "key"))
        self.assertIsNone(index_dict(123, "key"))
        self.assertIsNone(index_dict([], "key"))

    def test_index_dict_with_key_none(self):
        sample_dict = {"a": 1, None: "none_value"}
        self.assertEqual(index_dict(sample_dict, None), "none_value")

