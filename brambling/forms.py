from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db import models
from django.forms.models import inlineformset_factory
from django.template import loader
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
import floppyforms as forms

from brambling.models import (Event, Person, House, Item, ItemOption,
                              Discount, ItemDiscount)
from brambling.tokens import token_generators


FORMFIELD_OVERRIDES = {
    models.BooleanField: {'form_class': forms.BooleanField},
    models.CharField: {'form_class': forms.CharField},
    models.CommaSeparatedIntegerField: {'form_class': forms.CharField},
    models.DateField: {'form_class': forms.DateField},
    models.DateTimeField: {'form_class': forms.DateTimeField},
    models.DecimalField: {'form_class': forms.DecimalField},
    models.EmailField: {'form_class': forms.EmailField},
    models.FilePathField: {'form_class': forms.FilePathField},
    models.FloatField: {'form_class': forms.FloatField},
    models.IntegerField: {'form_class': forms.IntegerField},
    models.BigIntegerField: {'form_class': forms.IntegerField},
    models.IPAddressField: {'form_class': forms.IPAddressField},
    models.GenericIPAddressField: {'form_class': forms.GenericIPAddressField},
    models.NullBooleanField: {'form_class': forms.NullBooleanField},
    models.PositiveIntegerField: {'form_class': forms.IntegerField},
    models.PositiveSmallIntegerField: {'form_class': forms.IntegerField},
    models.SlugField: {'form_class': forms.SlugField},
    models.SmallIntegerField: {'form_class': forms.IntegerField},
    models.TextField: {'form_class': forms.CharField, 'widget': forms.Textarea},
    models.TimeField: {'form_class': forms.TimeField},
    models.URLField: {'form_class': forms.URLField},
    models.BinaryField: {'form_class': forms.CharField},

    models.FileField: {'form_class': forms.FileField},
    models.ImageField: {'form_class': forms.ImageField},

    models.ForeignKey: {'form_class': forms.ModelChoiceField},
    models.ManyToManyField: {'form_class': forms.ModelMultipleChoiceField},
    models.OneToOneField: {'form_class': forms.ModelChoiceField},
}


def formfield_callback(db_field, **kwargs):
    defaults = {'choices_form_class': forms.TypedChoiceField}
    defaults.update(FORMFIELD_OVERRIDES.get(db_field.__class__, {}))
    defaults.update(kwargs)
    return db_field.formfield(**defaults)


class EventForm(forms.ModelForm):
    formfield_callback = formfield_callback

    class Meta:
        model = Event
        exclude = ()


class BasePersonForm(forms.ModelForm):
    subject_template_name = "brambling/mail/email_confirm_subject.txt"
    body_template_name = "brambling/mail/email_confirm_body.txt"
    html_email_template_name = None
    generator = token_generators['email_confirm']

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(BasePersonForm, self).__init__(*args, **kwargs)

    def email_confirmation(self):
        if 'email' in self.changed_data:
            # Send confirmation link.
            context = {
                'person': self.instance,
                'pkb64': urlsafe_base64_encode(force_bytes(self.instance.pk)),
                'email': self.instance.email,
                'site': get_current_site(self.request),
                'token': self.generator.make_token(self.instance),
                'protocol': 'https' if self.request.is_secure() else 'http',
            }
            from_email = settings.DEFAULT_FROM_EMAIL

            subject = loader.render_to_string(self.subject_template_name,
                                              context)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            body = loader.render_to_string(self.body_template_name, context)

            if self.html_email_template_name:
                html_email = loader.render_to_string(self.html_email_template_name,
                                                     context)
            else:
                html_email = None
            send_mail(subject, body, from_email, [self.instance.email],
                      html_message=html_email)


class SignUpForm(BasePersonForm):
    formfield_callback = formfield_callback

    error_messages = {
        'duplicate_email': _("A user with that email already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
                                widget=forms.PasswordInput,
                                help_text=_("Enter the same password as above, for verification."))

    class Meta:
        model = Person
        fields = ('email', 'name',)

    def clean_email(self):
        # Since Person.email is unique, this check is redundant,
        # but it sets a nicer error message.
        email = self.cleaned_data["email"]
        q = models.Q(email=email) | models.Q(confirmed_email=email)
        if Person._default_manager.filter(q).exists():
            raise forms.ValidationError(
                self.error_messages['duplicate_email'],
                code='duplicate_email',
            )
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        person = super(SignUpForm, self).save(commit=False)
        person.set_password(self.cleaned_data["password1"])
        if commit:
            person.save()
            self.email_confirmation()
        return person


class PersonForm(BasePersonForm):
    formfield_callback = formfield_callback

    class Meta:
        model = Person
        exclude = ('created_timestamp', 'last_login', 'groups',
                   'user_permissions', 'password', 'is_superuser',
                   'confirmed_email')

    def save(self, commit=True):
        person = super(PersonForm, self).save(commit)
        if commit:
            self.email_confirmation()
        return person


class HouseForm(forms.ModelForm):
    formfield_callback = formfield_callback

    class Meta:
        model = House
        exclude = ()

    def __init__(self, person, *args, **kwargs):
        self.person = person
        super(HouseForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(HouseForm, self).save(commit)
        instance.residents.add(self.person)
        return instance


class ItemForm(forms.ModelForm):
    formfield_callback = formfield_callback

    class Meta:
        model = Item
        exclude = ('event',)

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(ItemForm, self).__init__(*args, **kwargs)

    def _post_clean(self):
        super(ItemForm, self)._post_clean()
        self.instance.event = self.event


ItemOptionFormSet = inlineformset_factory(Item, ItemOption, forms.ModelForm,
                                          exclude=(), extra=3,
                                          formfield_callback=formfield_callback)


class DiscountForm(forms.ModelForm):
    formfield_callback = formfield_callback
    autogenerate = forms.BooleanField()

    class Meta:
        model = Discount
        exclude = ('event', 'items')

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(DiscountForm, self).__init__(*args, **kwargs)
        if 'autogenerate' not in self.initial:
            self.initial['autogenerate'] = not self.instance.code
        self.fields['code'].required = False

    def _post_clean(self):
        super(DiscountForm, self)._post_clean()
        self.instance.event = self.event

    def save(self, commit=True):
        if (self.cleaned_data.get('autogenerate') or
                not self.cleaned_data.get('code')):
            code = get_random_string(6)
            while Discount.objects.filter(code=code).exists():
                code = get_random_string(6)
        self.instance.code = code
        return super(DiscountForm, self).save(commit)


ItemDiscountFormSet = inlineformset_factory(Discount, ItemDiscount,
                                            forms.ModelForm,
                                            exclude=(), extra=3,
                                            formfield_callback=formfield_callback)
