import datetime
from django.contrib.auth import login, authenticate
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
import floppyforms as forms
from floppyforms import inlineformset_factory

from brambling.models import (Event, Person, House, Item, ItemOption,
                              Discount, ItemDiscount, DanceStyle, EventType,
                              EventPerson, Date, EventHouse, PersonItem)
from brambling.utils import send_confirmation_email


class EventForm(forms.ModelForm):
    start_date = forms.DateField()
    end_date = forms.DateField()

    class Meta:
        model = Event
        exclude = ('dates', 'housing_dates', 'owner')
        widgets = {
            'country': forms.widgets.Select
        }

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].initial = getattr(self.instance, 'start_date', datetime.date.today)
        self.fields['end_date'].initial = getattr(self.instance, 'end_date', datetime.date.today)

    def clean(self):
        cd = self.cleaned_data
        if cd['start_date'] > cd['end_date']:
            raise forms.ValidationError("End date must be before or equal to "
                                        "the start date.")
        return cd

    def save(self):
        instance = super(EventForm, self).save()
        if {'start_date', 'end_date'} & set(self.changed_data):
            cd = self.cleaned_data
            date_set = {cd['start_date'] + datetime.timedelta(n - 1) for n in
                        xrange((cd['end_date'] - cd['start_date']).days + 2)}
            seen = set(Date.objects.filter(date__in=date_set
                                           ).values_list('date', flat=True))
            Date.objects.bulk_create([
                Date(date=date) for date in date_set
                if date not in seen
            ])
            instance.housing_dates = Date.objects.filter(date__in=date_set)
            date_set.remove(cd['start_date'] - datetime.timedelta(1))
            instance.dates = Date.objects.filter(date__in=date_set)
        return instance


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

    def save(self):
        person = super(SignUpForm, self).save(commit=False)
        person.set_password(self.cleaned_data["password1"])
        person.save()
        person.dance_styles = DanceStyle.objects.all()
        person.event_types = EventType.objects.all()
        self.email_confirmation()
        user = authenticate(email=self.cleaned_data['email'],
                            password=self.cleaned_data['password1'])
        login(self.request, user)
        return person


class PersonForm(BasePersonForm):
    class Meta:
        model = Person
        fields = ('email', 'name', 'nickname', 'phone', 'dance_styles',
                  'event_types', 'dietary_restrictions', 'ef_cause',
                  'ef_avoid_strong', 'ef_avoid_weak', 'person_prefer',
                  'person_avoid')

    def save(self, commit=True):
        person = super(PersonForm, self).save(commit)
        if commit:
            self.email_confirmation()
        return person


class HouseForm(forms.ModelForm):
    class Meta:
        model = House
        exclude = ()
        widgets = {
            'country': forms.widgets.Select
        }

    def __init__(self, person, *args, **kwargs):
        self.person = person
        super(HouseForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(HouseForm, self).save(commit)
        instance.residents.add(self.person)
        return instance


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        exclude = ('event',)

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(ItemForm, self).__init__(*args, **kwargs)

    def _post_clean(self):
        super(ItemForm, self)._post_clean()
        self.instance.event = self.event


ItemOptionFormSet = inlineformset_factory(Item, ItemOption)


class DiscountForm(forms.ModelForm):
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


ItemDiscountFormSet = inlineformset_factory(Discount, ItemDiscount)


class PersonItemForm(forms.ModelForm):
    """Lets a person choose item options to buy."""
    class Meta:
        model = PersonItem
        fields = ('quantity', 'owner',)

    def __init__(self, buyer, item_option, *args, **kwargs):
        super(PersonItemForm, self).__init__(*args, **kwargs)
        self.fields['owner'].initial = buyer
        self.buyer = buyer
        self.item_option = item_option

    def _post_clean(self):
        super(PersonItemForm, self)._post_clean()
        self.instance.buyer = self.buyer
        self.instance.item_option = self.item_option


class EventPersonForm(forms.ModelForm):
    class Meta:
        model = EventPerson
        exclude = ('event', 'person')
        widgets = {
            'bedtime': forms.RadioSelect,
            'wakeup': forms.RadioSelect,
        }


class EventHouseForm(forms.ModelForm):
    class Meta:
        model = EventHouse
        exclude = ('event', 'house')
