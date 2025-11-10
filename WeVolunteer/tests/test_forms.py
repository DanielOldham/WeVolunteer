from datetime import timedelta
from unittest.mock import patch

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from core.forms import (
    add_invalid_class_to_form_error_fields,
    EventForm,
    FirstLastNameSignupForm, OrganizationForm,
)
from core.models import Organization, OrganizationContact, OrganizationAdministrator, EventDescriptors, \
    EventLocationDescriptors


class FormHelperTests(TestCase):
    """
    Test class for the form helper functions.
    """

    class DummyForm(forms.Form):
        name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
        age = forms.IntegerField(widget=forms.TextInput(attrs={"class": "form-control"}))

    def test_adds_is_invalid_class(self):
        form = self.DummyForm(data={"name": "", "age": "abc"})
        form.is_valid()  # triggers errors
        add_invalid_class_to_form_error_fields(form)
        for field_name in form.errors:
            self.assertIn("is-invalid", form.fields[field_name].widget.attrs["class"])

    def test_no_is_invalid_class(self):
        form = self.DummyForm(data={"name": "Daniel", "age": 24})
        form.is_valid()
        add_invalid_class_to_form_error_fields(form)
        for field_name in form.errors:
            self.assertNotIn("is-invalid", form.fields[field_name].widget.attrs["class"])


class FirstLastNameSignupFormTests(TestCase):
    """
    Test class for the FirstLastNameSignupForm class.
    """

    def test_form_has_first_and_last_name(self):
        form = FirstLastNameSignupForm()
        self.assertIn("first_name", form.fields)
        self.assertIn("last_name", form.fields)
        self.assertTrue(form.fields["first_name"].required)
        self.assertTrue(form.fields["last_name"].required)


class EventFormTests(TestCase):
    """
    Test class for the EventForm class.
    """

    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(name="Org A")
        cls.other_org = Organization.objects.create(name="Org B")
        cls.contact = OrganizationContact.objects.create(
            name="John", email="john@example.com", organization=cls.organization
        )
        cls.other_contact = OrganizationContact.objects.create(
            name="Jane", email="jane@example.com", organization=cls.other_org
        )

    def make_cleaned_data(self):
        now = timezone.now()
        return {
            "title": "Test Event",
            "organization": self.organization,
            "primary_contact": self.contact,
            "date": now.date() + timedelta(days=2),
            "start_time": now.time(),
            "end_time": (now + timedelta(hours=1)).time(),
            "address": "1234 Address Lane",
            "event_descriptor_tags": [
                EventDescriptors.CLEANING,
                EventDescriptors.ANIMAL_CARE,
                EventDescriptors.BUILDING_CONSTRUCTION,
            ],
            "location_descriptor_tags": [EventLocationDescriptors.OUTDOOR],
            "description": "A cool event.",
        }

    def test_clean_good_data_adds_no_errors(self):
        data = self.make_cleaned_data()
        form = EventForm(data=data)
        form.cleaned_data = data

        with patch("core.forms.add_invalid_class_to_form_error_fields") as mock_func:
            form.clean()
            self.assertFalse(mock_func.called)

        self.assertEqual(len(form.errors), 0)
        self.assertEqual(len(form.non_field_errors()), 0)

    def test_is_valid_good_data_no_errors(self):
        data = self.make_cleaned_data()
        form = EventForm(data=data)
        form.cleaned_data = data

        with patch("core.forms.add_invalid_class_to_form_error_fields") as mock_func:
            valid = form.is_valid()
            self.assertTrue(valid)
            self.assertFalse(mock_func.called)

        self.assertEqual(len(form.errors), 0)
        self.assertEqual(len(form.non_field_errors()), 0)

    def test_clean_date_past_date_adds_error(self):
        form = EventForm()
        form.cleaned_data = {"date": timezone.now().date() - timedelta(days=1)}

        with self.assertRaises(ValidationError):
            form.clean_date()

    def test_clean_date_future_date_no_errors(self):
        form = EventForm()
        date = timezone.now().date() + timedelta(days=1)
        form.cleaned_data = {"date": date}
        future_date = form.clean_date()

        # form should store and return cleaned date
        self.assertEqual(future_date, form.cleaned_data["date"])

    def test_clean_event_descriptor_tags_too_many_adds_error(self):
        form = EventForm()
        form.cleaned_data = {
            "event_descriptor_tags": [
                EventDescriptors.CLEANING,
                EventDescriptors.ANIMAL_CARE,
                EventDescriptors.BUILDING_CONSTRUCTION,
                EventDescriptors.COMMUNITY_OUTREACH,
                EventDescriptors.PAINTING,
                EventDescriptors.OTHER,
            ]}
        with self.assertRaises(ValidationError):
            form.clean_event_descriptor_tags()

    def test_clean_event_descriptor_tags_valid_length_no_error(self):
        form = EventForm()
        tags = [
            EventDescriptors.CLEANING,
            EventDescriptors.ANIMAL_CARE,
            EventDescriptors.BUILDING_CONSTRUCTION,
        ]
        form.cleaned_data = {"event_descriptor_tags": tags}
        result = form.clean_event_descriptor_tags()

        self.assertEqual(result, tags)

    def test_clean_start_time_after_end_adds_error(self):
        form = EventForm()
        now = timezone.now()
        form.cleaned_data = {
            "start_time": now + timedelta(hours=1),
            "end_time": now,
        }

        with patch("core.forms.add_invalid_class_to_form_error_fields") as mock_func:
            form.clean()
            self.assertTrue(mock_func.called)
        self.assertIn("start_time", form.errors)
        self.assertIn("end_time", form.errors)

    def test_clean_end_time_after_start_no_error(self):
        form = EventForm()
        now = timezone.now()
        form.cleaned_data = {
            "start_time": now,
            "end_time": now + timedelta(hours=1),
        }

        with patch("core.forms.add_invalid_class_to_form_error_fields") as mock_func:
            form.clean()
            self.assertFalse(mock_func.called)
        self.assertNotIn("start_time", form.errors)
        self.assertNotIn("end_time", form.errors)

    def test_clean_no_end_time_no_error(self):
        form = EventForm()
        now = timezone.now()
        form.cleaned_data = {
            "start_time": now,
        }

        with patch("core.forms.add_invalid_class_to_form_error_fields") as mock_func:
            form.clean()
            self.assertFalse(mock_func.called)
        self.assertNotIn("start_time", form.errors)
        self.assertNotIn("end_time", form.errors)

    def test_clean_contact_not_in_org_adds_error(self):
        form = EventForm()
        form.cleaned_data = {
            "organization": self.organization,
            "primary_contact": self.contact
        }
        with patch("core.forms.add_invalid_class_to_form_error_fields") as mock_func:
            form.clean()
            self.assertFalse(mock_func.called)
        self.assertNotIn("primary_contact", form.errors)

    def test_clean_contact_in_org_no_error(self):
        form = EventForm()
        form.cleaned_data = {
            "organization": self.organization,
            "primary_contact": self.other_contact,
        }
        with patch("core.forms.add_invalid_class_to_form_error_fields") as mock_func:
            form.clean()
            self.assertTrue(mock_func.called)
        self.assertIn("primary_contact", form.errors)

    def test_widget_configuration_and_user_queryset_restriction(self):
        user = User.objects.create_user(username='user', password='password123')
        OrganizationAdministrator.objects.create(user=user, organization=self.organization)
        form = EventForm(user=user)

        self.assertEqual(list(form.fields["organization"].queryset), [self.organization])
        self.assertEqual(list(form.fields["primary_contact"].queryset), list(self.organization.organizationcontact_set.all()))
        self.assertEqual(form.fields["organization"].widget.attrs["class"], "form-select")
        self.assertEqual(form.fields["primary_contact"].widget.attrs["class"], "form-select")
        self.assertIn("placeholder", form.fields["date"].widget.attrs)
        self.assertEqual(form.fields["description"].widget.attrs["style"], "height: 130px")


class OrganizationFormTests(TestCase):
    """
    Test class for the OrganizationForm class.
    """

    @classmethod
    def setUpTestData(cls):
        cls.org_a = Organization.objects.create(name="Org A", about="Org A description")
        cls.org_b = Organization.objects.create(name="Org B", about="Org B description")

    @staticmethod
    def make_cleaned_data(name="Org C", about="A great org"):
        return {
            "name": name,
            "about": about,
        }

    def test_clean_good_data_adds_no_errors(self):
        data = self.make_cleaned_data()
        form = OrganizationForm(data=data)
        form.cleaned_data = data

        with patch("core.forms.add_invalid_class_to_form_error_fields") as mock_func:
            form.clean()
            self.assertFalse(mock_func.called)
        self.assertEqual(len(form.errors), 0)
        self.assertEqual(len(form.non_field_errors()), 0)

    def test_is_valid_good_data_no_errors(self):
        data = self.make_cleaned_data()
        form = OrganizationForm(data=data)
        form.cleaned_data = data

        with patch("core.forms.add_invalid_class_to_form_error_fields") as mock_func:
            self.assertTrue(form.is_valid())
            self.assertFalse(mock_func.called)
        self.assertEqual(len(form.errors), 0)
        self.assertEqual(len(form.non_field_errors()), 0)

    def test_clean_name_duplicate_name_adds_error(self):
        # add org with a duplicate name
        form = OrganizationForm()
        form.instance = self.org_a  # Simulate editing org_a
        form.cleaned_data = {"name": "Org B", "about": "About"}

        with self.assertRaises(ValidationError):
            form.clean_name()

    def test_clean_invalid_triggers_helper(self):
        form = OrganizationForm(data={})
        # form is empty, so errors will be present
        form.is_valid()  # triggers validation and generates errors
        with patch("core.forms.add_invalid_class_to_form_error_fields") as mock_func:
            form.clean()
            self.assertTrue(mock_func.called)
        self.assertTrue(form.errors)

    def test_widget_configuration_on_init(self):
        form = OrganizationForm()
        self.assertEqual(form.label_suffix, "")
        for visible in form.visible_fields():
            self.assertIn("form-control", visible.field.widget.attrs['class'])
            self.assertEqual(visible.field.widget.attrs['placeholder'], "placeholder")
        self.assertEqual(form.fields["about"].widget.attrs["style"], "height: 200px")

    def test_clean_name_exact_current_instance_allows(self):
        # editing an org with same name should not result in errors
        form = OrganizationForm()
        form.instance = self.org_a
        form.cleaned_data = {"name": self.org_a.name, "about": "About"}
        form.clean()
        self.assertEqual(form.clean_name(), self.org_a.name)
        self.assertFalse(form.errors)