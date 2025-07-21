from random import choices

from django.contrib.postgres.fields import ArrayField
from django.db import models
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.db.models import TextChoices


class EventDescriptorTags(TextChoices):
    """
    Enumeration of the different descriptive tags for an event.
    """

    MOVING = "MOVING", "Moving"
    YARD_WORK = "YARD_WORK", "Yard Work"
    CLEANING = "CLEANING", "Cleaning"
    FOOD_SERVICE = "FOOD_SERVICE", "Food Service"
    SETUP_TEARDOWN = "SETUP_TEARDOWN", "Setup/Teardown"
    HOMELESS_CARE = "HOMELESS_CARE", "Homeless Care"
    CHILDCARE = "CHILDCARE", "Childcare"
    ANIMAL_CARE = "ANIMAL_CARE", "Animal Care"
    FUNDRAISING = "FUNDRAISING", "Fundraising"
    COMMUNITY_OUTREACH = "COMMUNITY_OUTREACH", "Community Outreach"
    DONATION_SORTING = "DONATION_SORTING", "Donation Sorting"
    OFFICE_HELP ="OFFICE_HELP", "Office Help"
    ENVELOPE_STUFFING = "ENVELOPE_STUFFING", "Envelope Stuffing"
    FESTIVAL_SUPPORT = "FESTIVAL_SUPPORT", "Festival Support"
    RACE_CREW = "RACE_CREW", "Race Crew"
    PARKING_HELP = "PARKING_HELP", "Parking Help"
    BUILDING_CONSTRUCTION = "BUILDING_CONSTRUCTION", "Building/Construction"
    PAINTING = "PAINTING", "Painting"
    OTHER = "OTHER", "Other"


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        """
        Set the built-in username field equal to the email field.
        """
        user = super().populate_user(request, sociallogin, data)
        user.username = user.email
        return user


class MultipleChoiceArrayField(ArrayField):
    """
    Subclass Postgres ArrayField for Enum multiple choice functionality.
    """

    def formfield(self, **kwargs):
        from django import forms
        defaults = {
            "form_class": forms.MultipleChoiceField,
            "choices": self.base_field.choices,
        }
        defaults.update(kwargs)
        return super(ArrayField, self).formfield(**defaults)


class Organization(models.Model):
    """
    An organization in charge of events.
    """
    name = models.CharField(max_length=255)
    contact_phone = models.CharField(max_length=50, null=True, blank=True, verbose_name='contact phone number')
    contact_email = models.EmailField(null=True, blank=True, verbose_name='contact email')

    def __str__(self):
        return self.name


class Event(models.Model):
    """
    A single Volunteer event.
    """
    title = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField(verbose_name='start time')
    end_time = models.TimeField(verbose_name='end time', null=True, blank=True)
    # TODO: add Location model foreign key with location name, address, and address notes - can do active search for locations when choosing, or maybe just google maps api integration
    address = models.TextField(max_length=255, null=True, blank=True)
    # TODO: add indoor/outdoor/virtual tag field
    event_descriptor_tags = MultipleChoiceArrayField(
        models.CharField(max_length=50, choices=EventDescriptorTags),
        default=list,
        blank=True,
    )
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title + ' - ' + self.organization.__str__() + ' - ' + self.date.strftime('%m/%d/%Y')

