import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.models import construct_instance, BaseModelFormSet
from django.utils import timezone
import stripe
from zenaida import forms

from brambling.models import (Person, Home, Item, Discount,
                              EventPerson, Date, EventHousing, PersonItem,
                              PersonDiscount, EnvironmentalFactor,
                              HousingCategory, CreditCard, Payment)


CONFIRM_ERRORS = {'required': 'Must be marked correct.'}


class PersonDiscountForm(forms.ModelForm):
    discount = forms.CharField(max_length=20, label="discount code")

    class Meta:
        fields = ()
        model = PersonDiscount

    def __init__(self, event, person, *args, **kwargs):
        self.event = event
        self.person = person
        super(PersonDiscountForm, self).__init__(*args, **kwargs)

    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount is not None:
            now = timezone.now()
            try:
                discount = Discount.objects.filter(
                    code=discount,
                    event=self.event,
                ).filter(
                    (models.Q(available_start__lte=now) |
                     models.Q(available_start__isnull=True)),
                    (models.Q(available_end__gte=now) |
                     models.Q(available_end__isnull=True))
                ).get()
            except Discount.DoesNotExist:
                discount = None
        if discount is None:
            raise ValidationError("No discount with that code is currently "
                                  "active for this event.")
        return discount

    def _post_clean(self):
        self.instance.person = self.person
        if 'discount' in self.cleaned_data:
            self.instance.discount = self.cleaned_data['discount']
        super(PersonDiscountForm, self)._post_clean()


class OwnerForm(forms.ModelForm):
    class Meta:
        model = PersonItem
        fields = ('owner',)


# TODO: Must validate max_per_owner constraints.
class BaseOwnerFormSet(BaseModelFormSet):
    def __init__(self, default_owner, *args, **kwargs):
        super(BaseOwnerFormSet, self).__init__(*args, **kwargs)
        self.default_owner = default_owner

    def _construct_form(self, i, **kwargs):
        form = super(BaseOwnerFormSet, self)._construct_form(i, **kwargs)
        form.initial['owner'] = self.default_owner
        return form

OwnerFormSet = forms.modelformset_factory(PersonItem, OwnerForm, extra=0,
                                          formset=BaseOwnerFormSet)


class EventPersonForm(forms.MemoModelForm):
    """
    You only get to this form if housing data is being collected.

    There is always a guest subform. If you are the owner, there is
    also a host subform.

    """
    class Meta:
        model = EventPerson
        fields = ('car_spaces', 'bedtime', 'wakeup', 'housing')

    def __init__(self, personitem, event, memo_dict,
                 *args, **kwargs):
        self.event = event
        self.personitem = personitem
        self.memo_dict = memo_dict
        instance = EventPerson(person=personitem.owner, event=event,
                               event_pass=personitem)
        try:
            instance = self.get(EventPerson, person=personitem.owner,
                                event=event, event_pass=personitem)
        except EventPerson.DoesNotExist:
            pass
        kwargs['instance'] = instance
        super(EventPersonForm, self).__init__(memo_dict, *args, **kwargs)
        del kwargs['instance']

        self.guest_form = GuestForm(personitem, event, memo_dict,
                                    instance=instance, *args, **kwargs)

        if personitem.owner != personitem.buyer:
            self.fields['housing'].choices = self.fields['housing'].choices[:-1]
        else:
            self.host_form = HostingForm(personitem.owner.home, event, memo_dict,
                                         *args, **kwargs)

    def is_valid(self):
        valid = super(EventPersonForm, self).is_valid()
        if valid:
            if self.cleaned_data['housing'] == EventPerson.NEED:
                valid = self.guest_form.is_valid()
            elif (self.cleaned_data['housing'] == EventPerson.HOST and
                    hasattr(self, 'host_form')):
                valid = self.host_form.is_valid()
        return valid

    def save(self):
        instance = super(EventPersonForm, self).save()
        if instance.housing == EventPerson.NEED:
            self.guest_form.save()
        elif (instance.housing == EventPerson.HOST and
                hasattr(self, 'host_form')):
            self.host_form.save()
        self.personitem.is_completed = True
        self.personitem.save()
        return instance


class GuestForm(forms.MemoModelForm):
    ef_cause_confirm = forms.BooleanField(initial=False,
                                          error_messages=CONFIRM_ERRORS)
    ef_avoid_confirm = forms.BooleanField(initial=False,
                                          error_messages=CONFIRM_ERRORS)

    class Meta:
        model = EventPerson
        exclude = ('event', 'person', 'car_spaces',
                   'bedtime', 'wakeup', 'housing', 'event_pass')
        error_messages = {
            'ef_cause_confirm': {'required': 'Must be marked correct.'},
            'ef_avoid_confirm': {'required': 'Must be marked correct.'},
        }

    def __init__(self, personitem, event, memo_dict,
                 *args, **kwargs):
        self.personitem = personitem
        self.event = event
        self.memo_dict = memo_dict

        super(GuestForm, self).__init__(memo_dict, *args, **kwargs)
        if personitem.buyer == personitem.owner:
            self.fields['save_as_defaults'] = forms.BooleanField(initial=True)
            if self.instance.pk is None:
                owner = self.personitem.owner
                self.initial.update({
                    'ef_cause': owner.ef_cause.all(),
                    'ef_avoid': owner.ef_avoid.all(),
                    'person_prefer': owner.person_prefer.all(),
                    'person_avoid': owner.person_avoid.all(),
                    'housing_prefer': owner.housing_prefer.all(),
                    'other_needs': owner.other_needs,
                })
                self.instance.event = event
                self.instance.person = owner
        self.fields['nights'].required = True
        self.set_choices('nights', Date, event_housing_dates=event)
        self.set_choices('person_prefer',
                         Person.objects.only('id', 'name'))
        self.set_choices('person_avoid',
                         Person.objects.only('id', 'name'))
        self.set_choices('ef_cause',
                         EnvironmentalFactor.objects.only('id', 'name'))
        self.set_choices('ef_avoid',
                         EnvironmentalFactor.objects.only('id', 'name'))
        self.set_choices('housing_prefer',
                         HousingCategory.objects.only('id', 'name'))

    def save(self):
        instance = super(GuestForm, self).save()
        if (self.personitem.owner == self.personitem.buyer and
                self.cleaned_data['save_as_defaults']):
            owner = self.personitem.owner
            owner.ef_cause = instance.ef_cause.all()
            owner.ef_avoid = instance.ef_avoid.all()
            owner.person_prefer = instance.person_prefer.all()
            owner.person_avoid = instance.person_avoid.all()
            owner.housing_prefer = instance.housing_prefer.all()
            owner.other_needs = instance.other_needs
            owner.save()
        return instance


class HostingForm(forms.MemoModelForm):
    housing_categories_confirm = forms.BooleanField(initial=False,
                                                    error_messages=CONFIRM_ERRORS)
    ef_present_confirm = forms.BooleanField(initial=False,
                                            error_messages=CONFIRM_ERRORS)
    ef_avoid_confirm = forms.BooleanField(initial=False,
                                          error_messages=CONFIRM_ERRORS)
    save_as_defaults = forms.BooleanField(initial=True)

    class Meta:
        model = EventHousing
        exclude = ('event', 'home')

    def __init__(self, home, event, memo_dict, *args, **kwargs):
        self.home = home
        self.memo_dict = memo_dict
        try:
            qs = EventHousing.objects.prefetch_related(
                'ef_present', 'ef_avoid', 'person_prefer',
                'person_avoid', 'housing_categories', 'nights')
            kwargs['instance'] = self.get(qs,
                                          event=event,
                                          home=home)
        except EventHousing.DoesNotExist:
            kwargs['instance'] = None
        super(HostingForm, self).__init__(memo_dict, *args, **kwargs)
        if self.instance.pk is None and home is not None:
            self.initial.update({
                'ef_present': home.ef_present.all(),
                'ef_avoid': home.ef_avoid.all(),
                'person_prefer': home.person_prefer.all(),
                'person_avoid': home.person_avoid.all(),
                'housing_categories': home.housing_categories.all(),
            })
            self.instance.event = event
            self.instance.home = home
        self.fields['nights'].required = True
        self.set_choices('nights', Date, event_housing_dates=event)
        self.set_choices('person_prefer',
                         Person.objects.only('id', 'name'))
        self.set_choices('person_avoid',
                         Person.objects.only('id', 'name'))
        self.set_choices('ef_present',
                         EnvironmentalFactor.objects.only('id', 'name'))
        self.set_choices('ef_avoid',
                         EnvironmentalFactor.objects.only('id', 'name'))
        self.set_choices('housing_categories',
                         HousingCategory.objects.only('id', 'name'))

    def save(self):
        instance = super(HostingForm, self).save()
        if self.cleaned_data['save_as_defaults']:
            self.home.ef_present = instance.ef_present.all()
            self.home.ef_avoid = instance.ef_avoid.all()
            self.home.person_prefer = instance.person_prefer.all()
            self.home.person_avoid = instance.person_avoid.all()
            self.home.housing_categories = instance.housing_categories.all()
            self.home.save()
        return instance


import floppyforms as forms


class CheckoutForm(forms.Form):
    card = forms.ModelChoiceField(CreditCard)

    def __init__(self, event, person, balance, *args, **kwargs):
        super(CheckoutForm, self).__init__(*args, **kwargs)
        self.person = person
        self.event = event
        self.balance = balance
        self.fields['card'].queryset = person.cards.all()
        self.fields['card'].initial = person.default_card

        if self.balance <= 0:
            del self.fields['card']

    def clean(self):
        cleaned_data = super(CheckoutForm, self).clean()
        cart = self.person.get_cart(self.event)
        if cart is not None and not cart.is_finalized():
            raise ValidationError("Cart must be finalized before paying.")
        return cleaned_data

    def save(self):
        if self.balance <= 0:
            return
        card = self.cleaned_data['card']
        stripe.api_key = settings.STRIPE_SECRET_KEY
        charge = stripe.Charge.create(
            amount=int(self.balance * 100),
            currency=self.event.currency,
            customer=self.person.stripe_customer_id,
            card=card.stripe_card_id,
        )
        payment = Payment.objects.create(event=self.event,
                                         person=self.person,
                                         amount=self.balance,
                                         stripe_charge_id=charge.id)
        return payment
