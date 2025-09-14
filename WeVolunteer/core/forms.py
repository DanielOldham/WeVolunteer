from bootstrap_datepicker_plus.widgets import DatePickerInput, TimePickerInput
from django import forms
from allauth.account.forms import SignupForm
from django.contrib.auth.models import User

from core.models import Event, Organization, OrganizationContact, OrganizationAdministrator


class FirstLastNameSignupForm(SignupForm):
    """
    Signup form containing first and last name.
    Extends Allauth SignupForm.
    """

    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)


class EventForm(forms.ModelForm):
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
        self.label_suffix = ""

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = 'placeholder'

        if user is not None:
            queryset = OrganizationAdministrator.objects.filter(user=user)
            if queryset.exists():
                organization = queryset.first().organization
                self.fields["organization"].queryset = Organization.objects.filter(id=organization.id)
                self.fields["primary_contact"].queryset = OrganizationContact.objects.filter(organization=organization)

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