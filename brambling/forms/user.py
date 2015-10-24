from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm,
                                       SetPasswordForm)
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
import floppyforms.__future__ as forms

from brambling.mail import ConfirmationMailer
from brambling.models import Person, Home, DanceStyle
from brambling.utils.international import clean_postal_code
from brambling.utils.payment import LIVE


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


class SignUpForm(forms.ModelForm):
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

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(SignUpForm, self).__init__(*args, **kwargs)

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
        if 'email' in self.changed_data:
            ConfirmationMailer(
                person=self.instance,
                site=get_current_site(self.request),
                secure=self.request.is_secure()
            ).send([self.instance.email])
        user = authenticate(email=self.cleaned_data['email'],
                            password=self.cleaned_data['password1'])
        login(self.request, user)
        return person


class AccountForm(forms.ModelForm):
    error_messages = {
        'password_incorrect': _("Your old password was entered incorrectly. "
                                "Please enter it again."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    old_password = forms.CharField(label=_("Old password"),
                                   widget=forms.PasswordInput,
                                   required=False)
    new_password1 = forms.CharField(label=_("New password"),
                                    widget=forms.PasswordInput,
                                    required=False)
    new_password2 = forms.CharField(label=_("New password confirmation"),
                                    widget=forms.PasswordInput,
                                    required=False)

    class Meta:
        model = Person
        fields = ('email', 'given_name', 'middle_name', 'surname', 'name_order')

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(AccountForm, self).__init__(*args, **kwargs)

    def clean_old_password(self):
        """
        Validates that the old_password field is correct (if provided).
        """
        old_password = self.cleaned_data["old_password"]
        if old_password and not self.instance.check_password(old_password):
            raise ValidationError(
                self.error_messages['password_incorrect'],
                code='password_incorrect',
            )
        return old_password

    def clean_new_password2(self):
        """
        Validates that the passwords are the same and that the old_password
        field was also provided.
        """
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        if self.cleaned_data.get('new_password1'):
            self.instance.set_password(self.cleaned_data['new_password1'])
        person = super(AccountForm, self).save(commit)
        if commit and 'email' in self.changed_data:
            ConfirmationMailer(
                person=self.instance,
                site=get_current_site(self.request),
                secure=self.request.is_secure()
            ).send([self.instance.email])
        return person


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ('given_name', 'middle_name', 'surname', 'name_order')


class BillingForm(forms.ModelForm):
    disconnect_dwolla = forms.BooleanField(required=False)

    class Meta:
        model = Person
        fields = ()

    def __init__(self, *args, **kwargs):
        super(BillingForm, self).__init__(*args, **kwargs)
        if not self.instance.dwolla_user_id:
            del self.fields['disconnect_dwolla']

    def save(self, commit=True):
        if self.cleaned_data.get('disconnect_dwolla'):
            self.instance.clear_dwolla_data(LIVE)
        return super(BillingForm, self).save(commit)


class HomeForm(forms.ModelForm):
    class Meta:
        model = Home
        exclude = ()
        widgets = {
            'country': forms.Select
        }

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(HomeForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(HomeForm, self).clean()
        if 'country' in cleaned_data and 'zip_code' in cleaned_data:
            country = cleaned_data['country']
            code = cleaned_data['zip_code']
            try:
                cleaned_data['zip_code'] = clean_postal_code(country, code)
            except ValidationError, e:
                del cleaned_data['zip_code']
                self.add_error('zip_code', e)
        return cleaned_data

    def save(self, commit=True):
        instance = super(HomeForm, self).save(commit)
        if self.request.user.home_id is None:
            self.request.user.home = instance
            self.request.user.save()
        return instance
