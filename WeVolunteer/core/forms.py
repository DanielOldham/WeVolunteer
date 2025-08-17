from django import forms
from allauth.account.forms import SignupForm

class FirstLastNameSignupForm(SignupForm):
    """
    Signup form containing first and last name.
    Extends Allauth SignupForm.
    """

    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)