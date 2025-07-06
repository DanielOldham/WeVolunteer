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
