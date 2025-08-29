from django import forms
from allauth.account.forms import SignupForm

from core.models import Event


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

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.label_suffix = ""
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            visible.field.widget.attrs['placeholder'] = 'placeholder'