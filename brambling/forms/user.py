from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm,
                                       SetPasswordForm)
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
import floppyforms.__future__ as forms

from brambling.models import Person, Home, DanceStyle
from brambling.utils import send_confirmation_email


class FloppyAuthenticationForm(AuthenticationForm):
    username = forms.CharField(max_length=254)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)


class FloppyPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label=_("Email"), max_length=254)


class FloppySetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label=_("New password"),
                                    widget=forms.PasswordInput)
    new_password2 = forms.CharField(label=_("Confirm password"),
                                    widget=forms.PasswordInput)


class BasePersonForm(forms.ModelForm):
    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(BasePersonForm, self).__init__(*args, **kwargs)

    def email_confirmation(self):
        if 'email' in self.changed_data:
            send_confirmation_email(self.instance, self.request,
                                    secure=self.request.is_secure())


class SignUpForm(BasePersonForm):
    error_messages = {
        'duplicate_email': _("A user with that email already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
                                widget=forms.PasswordInput,
                                help_text=_("Enter the same password as above,"
                                            " for verification."))

    class Meta:
        model = Person
        fields = (
            'email',
            'given_name',
            'middle_name',
            'surname',
            'name_order'
        )

    def clean_email(self):
        # Since Person.email is unique, this check is redundant,
        # but it sets a nicer error message.
        email = self.cleaned_data["email"]
        q = models.Q(email=email) | models.Q(confirmed_email=email)
        if Person._default_manager.filter(q).exists():
            raise ValidationError(
                self.error_messages['duplicate_email'],
                code='duplicate_email',
            )
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self):
        person = super(SignUpForm, self).save(commit=False)
        person.set_password(self.cleaned_data["password1"])
        person.save()
        person.dance_styles = DanceStyle.objects.all()
        self.email_confirmation()
        user = authenticate(email=self.cleaned_data['email'],
                            password=self.cleaned_data['password1'])
        login(self.request, user)
        return person


class PersonForm(BasePersonForm):
    disconnect_dwolla = forms.BooleanField(required=False)

    class Meta:
        model = Person
        fields = ('email', 'given_name', 'middle_name', 'surname', 'name_order',
                  'phone', 'dance_styles', 'dietary_restrictions', 'ef_cause',
                  'ef_avoid', 'person_prefer', 'person_avoid',
                  'housing_prefer', 'other_needs')

    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        self.STRIPE_APPLICATION_ID = getattr(settings, 'STRIPE_APPLICATION_ID', None)
        if not self.instance.dwolla_user_id:
            del self.fields['disconnect_dwolla']

    def save(self, commit=True):
        self.instance.modified_directly = True
        person = super(PersonForm, self).save(commit)
        if commit:
            self.email_confirmation()
        return person


class HomeForm(forms.ModelForm):
    class Meta:
        model = Home
        exclude = ()
        widgets = {
            'country': forms.Select
        }

    def __init__(self, person, *args, **kwargs):
        self.person = person
        super(HomeForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(HomeForm, self).save(commit)
        instance.residents.add(self.person)
        return instance
