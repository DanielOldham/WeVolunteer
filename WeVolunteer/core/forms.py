from bootstrap_datepicker_plus.widgets import DatePickerInput, TimePickerInput
from django import forms
from allauth.account.forms import SignupForm
from django.core.exceptions import ValidationError
from django.forms import Form
from django.utils import timezone

from core.models import Event, Organization, OrganizationContact, OrganizationAdministrator


def add_invalid_class_to_form_error_fields(form: Form):
    """
    Helper function to add the Bootstrap is-invalid class to all fields in the given form with errors.
    """

    for field in form.errors:
        current_class = form.fields[field].widget.attrs["class"]
        form.fields[field].widget.attrs["class"] = current_class + " is-invalid"


class FirstLastNameSignupForm(SignupForm):
    """
    Signup form containing first and last name.
    Extends Allauth SignupForm.
    """

    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)


class EventForm(forms.ModelForm):
    """
    Django ModelForm for adding or editing an Event.
    """

    past_date_error = "Date must not be in the past"
    start_time_error = "Start time must be before end time"
    end_time_error = "End time must be after start time"

    def clean(self):
        """
        Form level clean method.
        """

        cleaned_data = super().clean()

        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        if end_time:
            if start_time > end_time:
                self.add_error("start_time", self.start_time_error)
                self.add_error("end_time", self.end_time_error)

        organization = cleaned_data.get("organization")
        primary_contact = cleaned_data.get("primary_contact")
        if primary_contact is not None:
            if primary_contact.organization != organization:
                self.add_error("primary_contact", "Primary contact must belong to this event's organization")

        if self.errors:
            add_invalid_class_to_form_error_fields(self)

    def clean_date(self):
        """
        Clean method for the date field.
        """

        date = self.cleaned_data["date"]
        if date < timezone.now().date():
            raise ValidationError(self.past_date_error)
        return date

    def clean_event_descriptor_tags(self):
        """
        Clean method for the event_descriptor_tags field.
        """

        tags = self.cleaned_data["event_descriptor_tags"]
        if len(tags) > 5:
            raise ValidationError("You may only select up to 5 descriptive tags")
        return tags

    class Meta:
        model = Event
        fields = "__all__"
        widgets = {
            "date": DatePickerInput(options={"format": "MM-DD-YYYY"}),
            "start_time": TimePickerInput(options={"format": "hh:mm A"}),
            "end_time": TimePickerInput(options={"format": "hh:mm A"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(EventForm, self).__init__(*args, **kwargs)

        # if user is org admin (not superuser), set possible organization and primary contact fields to allowed queryset
        if user is not None:
            queryset = OrganizationAdministrator.objects.filter(user=user)
            if queryset.exists():
                organization = queryset.first().organization
                self.fields["organization"].queryset = Organization.objects.filter(id=organization.id)
                self.fields["primary_contact"].queryset = OrganizationContact.objects.filter(organization=organization)

        self.label_suffix = ""
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = 'placeholder'

        self.fields["organization"].widget.attrs["class"] = "form-select"
        self.fields["organization"].empty_label = None
        self.fields["primary_contact"].widget.attrs["class"] = "form-select"
        self.fields["primary_contact"].empty_label = "Unassigned"
        self.fields["date"].widget.attrs["placeholder"] = "Date (DD-MM-YYYY)"
        self.fields["start_time"].widget.attrs["placeholder"] = "Start Time (hh:mm AM)"
        self.fields["end_time"].widget.attrs["placeholder"] = "End Time (hh:mm AM)"
        self.fields["event_descriptor_tags"].widget.attrs["data-bind"] = "event_descriptor_tags"
        self.fields["location_descriptor_tags"].widget.attrs["data-bind"] = "location_descriptor_tags"
        self.fields["description"].widget.attrs["style"] = "height: 130px"
