import datetime

from django import forms
from django.db import models
from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import MagicMock, patch

from core.models import (
    EventDescriptors,
    EventLocationDescriptors,
    TimeOfDay,
    time_of_day_ranges,
    ranges_overlap,
    point_in_range,
    get_time_of_day_enum_list,
    CustomSocialAccountAdapter,
    MultipleChoiceArrayField,
    Organization,
    OrganizationContact,
    OrganizationAdministrator,
    Event,
)


class UtilityFunctionTests(TestCase):
    """
    Test class for the models utility functions.
    """

    def test_ranges_overlap_true_and_false(self):
        # overlap
        self.assertTrue(ranges_overlap(1, 5, 4, 10))
        # no overlap
        self.assertFalse(ranges_overlap(1, 2, 3, 4))

    def test_point_in_range_true_and_false(self):
        self.assertTrue(point_in_range(5, 1, 10))
        self.assertFalse(point_in_range(0, 1, 10))

    def test_get_time_of_day_enum_list_empty_and_single_value(self):
        t = datetime.time(6, 30)
        result = get_time_of_day_enum_list(time_1=t)
        self.assertEqual(result, [TimeOfDay.MORNING])

    def test_get_time_of_day_enum_list_range_overlaps_all_blocks(self):
        start = datetime.time(0, 0)
        end = datetime.time(23, 59)
        result = get_time_of_day_enum_list(start, end)
        for key in TimeOfDay:  # type: ignore[attr-defined]
            self.assertIn(key, result)


class EnumTests(TestCase):
    """
    Test class for the TextChoices enums.
    """

    def test_event_descriptor_values(self):
        self.assertIn("MOVING", EventDescriptors.values) # type: ignore[attr-defined]
        self.assertTrue(EventDescriptors.MOVING.label, "Moving")

    def test_event_location_descriptors(self):
        labels = [choice.label for choice in EventLocationDescriptors] # type: ignore[attr-defined]
        self.assertIn("Indoor", labels)
        self.assertIn("Outdoor", labels)
        self.assertIn("Virtual", labels)

    def test_time_of_day_enum_labels_and_ranges(self):
        all_labels = [t.label for t in TimeOfDay] # type: ignore[attr-defined]
        self.assertIn("Morning", all_labels)
        self.assertEqual(
            time_of_day_ranges[TimeOfDay.MORNING],
            (datetime.time(6, 0, 0), datetime.time(9, 59, 59)),
        )


class CustomSocialAccountAdapterTests(TestCase):
    """
    Test class for the custom social account adapter.
    """

    def setUp(self):
        self.adapter = CustomSocialAccountAdapter()
        self.mock_request = MagicMock()
        self.mock_social_login = MagicMock()
        self.mock_data = {"email": "hello@example.com"}

    @patch("core.models.DefaultSocialAccountAdapter.populate_user")
    def test_populate_user_sets_username_to_email(self, mock_super_populate):
        # Prepare the fake user object returned from super().populate_user
        mock_user = MagicMock()
        mock_user.email = "john@example.com"
        mock_user.username = None
        mock_super_populate.return_value = mock_user

        # Call method under test
        result = self.adapter.populate_user(self.mock_request, self.mock_social_login, self.mock_data)

        # Assert super was called properly
        mock_super_populate.assert_called_once_with(self.mock_request, self.mock_social_login, self.mock_data)
        # Assert username was updated to match email
        self.assertEqual(result.username, "john@example.com")
        self.assertEqual(result.email, "john@example.com")
        # Assert the returned object is the same user instance
        self.assertIs(result, mock_user)


class MultipleChoiceArrayFieldTests(TestCase):
    """
    Test class for the custom multiple choice array field class.
    """

    def test_formfield_returns_multiple_choice_field(self):
        base_field = models.CharField(choices=[("A", "Alpha"), ("B", "Beta")])
        field = MultipleChoiceArrayField(base_field)
        form_field = field.formfield()
        self.assertIsInstance(form_field, forms.MultipleChoiceField)
        self.assertEqual(form_field.choices, [("A", "Alpha"), ("B", "Beta")])
        self.assertIn("form_class", {"form_class": forms.MultipleChoiceField})


class ModelStringMethodTests(TestCase):
    """
    Test class for various model string methods.
    """

    def setUp(self):
        self.organization = Organization.objects.create(name="Test Org")
        self.contact = OrganizationContact.objects.create(
            organization=self.organization,
            name="John Doe",
            email="john@example.com",
        )
        self.admin_user = User.objects.create(username="orgadmin", email="admin@example.com")
        self.org_admin = OrganizationAdministrator.objects.create(
            user=self.admin_user, organization=self.organization
        )
        self.event = Event.objects.create(
            title="Charity Run",
            organization=self.organization,
            primary_contact=self.contact,
            date=datetime.date.today(),
            start_time=datetime.time(10, 0),
            end_time=datetime.time(12, 0),
            event_descriptor_tags=[EventDescriptors.CLEANING],
            location_descriptor_tags=[EventLocationDescriptors.INDOOR],
            description="Helping out",
        )

    def test_organization_str(self):
        self.assertEqual(str(self.organization), "Test Org")

    def test_contact_str(self):
        self.assertEqual(str(self.contact), "John Doe (Test Org)")

    def test_event_str_repr_and_time_of_day(self):
        s = str(self.event)
        self.assertIn("Charity Run", s)
        self.assertIn(self.organization.name, s)
        tod = self.event.time_of_day()
        self.assertIn(TimeOfDay.MID_MORNING, tod)

    def test_organization_admin_link(self):
        self.assertEqual(self.org_admin.organization, self.organization)
        self.assertEqual(self.org_admin.user, self.admin_user)


class TimeOfDayRangeEdgeCasesTests(TestCase):
    def test_point_in_each_range_returns_expected_enum(self):
        times = [
            (datetime.time(0, 30), TimeOfDay.EARLY_MORNING),
            (datetime.time(6, 1), TimeOfDay.MORNING),
            (datetime.time(10, 30), TimeOfDay.MID_MORNING),
            (datetime.time(12, 30), TimeOfDay.MIDDAY),
            (datetime.time(15, 0), TimeOfDay.AFTERNOON),
            (datetime.time(18, 30), TimeOfDay.EVENING),
            (datetime.time(22, 0), TimeOfDay.NIGHT),
        ]
        for time, expected in times:
            enum_list = get_time_of_day_enum_list(time)
            self.assertEqual(enum_list, [expected])
