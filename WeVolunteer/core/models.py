import datetime
from random import choices

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.db.models import TextChoices


class EventDescriptors(TextChoices):
    """
    Enumeration for the different event descriptor tags.
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
    OFFICE_HELP = "OFFICE_HELP", "Office Help"
    ENVELOPE_STUFFING = "ENVELOPE_STUFFING", "Envelope Stuffing"
    FESTIVAL_SUPPORT = "FESTIVAL_SUPPORT", "Festival Support"
    RACE_CREW = "RACE_CREW", "Race Crew"
    PARKING_HELP = "PARKING_HELP", "Parking Help"
    BUILDING_CONSTRUCTION = "BUILDING_CONSTRUCTION", "Building/Construction"
    PAINTING = "PAINTING", "Painting"
    OTHER = "OTHER", "Other"


class EventLocationDescriptors(TextChoices):
    """
    Enumeration for the different event location descriptor tags.
    """

    INDOOR = "INDOOR", "Indoor"
    OUTDOOR = "OUTDOOR", "Outdoor"
    VIRTUAL = "VIRTUAL", "Virtual"


class TimeOfDay(TextChoices):
    """
    Enumeration for different time block descriptions.
    """

    EARLY_MORNING = "EARLY_MORNING", "Early Morning"
    MORNING = "MORNING", "Morning"
    MID_MORNING = "MID_MORNING", "Mid-Morning"
    MIDDAY = "MIDDAY", "Midday"
    AFTERNOON = "AFTERNOON", "Afternoon"
    EVENING = "EVENING", "Evening"
    NIGHT = "NIGHT", "Night"


# TimeOfDay ranges
# 12AM-06AM : Early Morning
# 06AM-10AM : Morning
# 10AM-12AM : Mid-Morning
# 12PM-02PM : Midday
# 02PM-06PM : Afternoon
# 06PM-08PM : Evening
# 08PM-12AM : Night
time_of_day_ranges = {
    TimeOfDay.EARLY_MORNING: (datetime.time(0, 0, 0), datetime.time(5, 59, 59)),
    TimeOfDay.MORNING: (datetime.time(6, 0,0), datetime.time(9, 59, 59)),
    TimeOfDay.MID_MORNING: (datetime.time(10, 0,0), datetime.time(11, 59, 59)),
    TimeOfDay.MIDDAY: (datetime.time(12, 0, 0), datetime.time(13, 59, 59)),
    TimeOfDay.AFTERNOON: (datetime.time(14, 0, 0), datetime.time(17, 59, 59)),
    TimeOfDay.EVENING: (datetime.time(18, 0, 0), datetime.time(19, 59, 59)),
    TimeOfDay.NIGHT: (datetime.time(20, 0, 0), datetime.time(23, 59, 59)),
}


def ranges_overlap(range_1_start, range_1_end, range_2_start, range_2_end):
    """
    Check if two ranges overlap.

    :param range_1_start: start of the first range
    :param range_1_end: end of the first range
    :param range_2_start: start of the second range
    :param range_2_end: end of the second range
    :return: True if the ranges overlap, False otherwise
    """

    return range_1_start <= range_2_end and range_1_end >= range_2_start


def point_in_range(point, range_start, range_end):
    """
    Check if a point is within a range.

    :param point: point to check
    :param range_start: start of the range
    :param range_end: end of the range
    :return: True if the point is within range, False otherwise
    """

    return range_start <= point <= range_end


def get_time_of_day_enum_list(time_1 : datetime.time, time_2 : datetime.time=None) -> list[TimeOfDay]:
    """
    Get a list of TimeOfDay Enum objects that the range of given datetime.time objects overlap with.
    If only passing one time object, return a single item list containing the TimeOfDay range it falls in.

    :param time_1: start of the range
    :param time_2: end of the range
    :return: list of TimeOfDay Enum objects
    """

    if not time_1 and not time_2:
        return []
    if not time_1 or not time_2: # if either null/empty
        time = time_1 if time_1 else time_2
        for key, value in time_of_day_ranges.items():
            if point_in_range(time, value[0], value[1]):
                return [key]
    else:
        enum_list = []
        for key, value in time_of_day_ranges.items():
            if ranges_overlap(time_1, time_2, value[0], value[1]):
                enum_list.append(key)

        return enum_list


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
    # contact_phone = models.CharField(max_length=50, null=True, blank=True, verbose_name='contact phone number')
    # contact_email = models.EmailField(null=True, blank=True, verbose_name='contact email')

    def __str__(self):
        return self.name

class OrganizationContact(models.Model):
    """
    A single contact for an organization.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True, verbose_name='phone number')
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name + " (" + self.organization.name + ")"


class OrganizationAdministrator(models.Model):
    """
    A connection between an Organization and one single administrating User account.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)



class Event(models.Model):
    """
    A single Volunteer event.
    """
    title = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    primary_contact = models.ForeignKey(OrganizationContact, blank=True, null=True, on_delete=models.SET_NULL)
    date = models.DateField()
    start_time = models.TimeField(verbose_name='start time')
    end_time = models.TimeField(verbose_name='end time', null=True, blank=True)
    # TODO: add Location model foreign key with location name, address, and address notes - can do active search for locations when choosing, or maybe just google maps api integration
    address = models.TextField(max_length=255, null=True, blank=True)
    event_descriptor_tags = MultipleChoiceArrayField(
        models.CharField(max_length=50, choices=EventDescriptors),
        default=list,
        blank=True,
    )
    location_descriptor_tags = MultipleChoiceArrayField(
        models.CharField(max_length=20, choices=EventLocationDescriptors),
        default=list,
        blank=True,
    )
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title + ' - ' + self.organization.__str__() + ' - ' + self.date.strftime('%m/%d/%Y')

    def time_of_day(self):
        return get_time_of_day_enum_list(self.start_time, self.end_time)

