from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

class NoSignupExceptGoogleAdapter(DefaultAccountAdapter):
    """
    Account Adapter to disable allauth signup unless user is signing up with Google integration.
    Needed for staging.
    """

    def is_open_for_signup(self, request):
        # disable the regular signup page, leave google signup open
        if request and request.path.rstrip('/') == reverse('account_signup').rstrip('/'):
            return False
        return super().is_open_for_signup(request)
