from django.db import models
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        """
        Set the built-in username field equal to the email field.
        """
        user = super().populate_user(request, sociallogin, data)
        user.username = user.email
        return user

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
    # TODO: add Location model foreign key with location name, address, and address notes - can do active search for locations when choosing
    address = models.TextField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title + ' - ' + self.organization.__str__() + ' - ' + self.date.strftime('%m/%d/%Y')

