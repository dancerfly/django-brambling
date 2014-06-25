from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
import floppyforms.__future__ as forms
import stripe
from zenaida.forms import MemoModelForm

from brambling.models import (Date, EventHousing, EnvironmentalFactor,
                              HousingCategory, CreditCard, Payment, Home,
                              Attendee, HousingSlot)


CONFIRM_ERROR = "Please check this box to confirm the value is correct"


class AttendeeBasicDataForm(forms.ModelForm):
    class Meta:
        model = Attendee

    def __init__(self, *args, **kwargs):
        super(AttendeeBasicDataForm, self).__init__(*args, **kwargs)
        self.fields['liability_waiver'].required = True


class AttendeeHousingDataForm(MemoModelForm):
    class Meta:
        model = Attendee
        fields = ('nights', 'ef_cause', 'ef_avoid', 'person_prefer',
                  'person_avoid', 'housing_prefer', 'other_needs')

    def __init__(self, *args, **kwargs):
        super(AttendeeHousingDataForm, self).__init__(*args, **kwargs)

        if self.instance.person == self.instance.event_person.person:
            self.fields['save_as_defaults'] = forms.BooleanField(initial=True)

            if not self.instance.housing_completed:
                if self.instance.person.modified_directly:
                    self.fields['ef_cause_confirm'] = forms.BooleanField(
                        required=True,
                        error_messages={'required': CONFIRM_ERROR},
                        label="Is this still correct?",
                    )
                    self.fields['ef_avoid_confirm'] = forms.BooleanField(
                        required=True,
                        error_messages={'required': CONFIRM_ERROR},
                        label="Is this still correct?",
                    )

                owner = self.instance.person
                self.initial.update({
                    'ef_cause': self.filter(EnvironmentalFactor.objects.only('id'),
                                            person_cause=owner),
                    'ef_avoid': self.filter(EnvironmentalFactor.objects.only('id'),
                                            person_avoid=owner),
                    'person_prefer': owner.person_prefer,
                    'person_avoid': owner.person_prefer,
                    'housing_prefer': self.filter(HousingCategory.objects.only('id'),
                                                  preferred_by=owner),
                    'other_needs': owner.other_needs,
                })

        self.fields['nights'].required = True
        self.set_choices('nights', Date, event_housing_dates=self.instance.event_person.event)
        self.set_choices('ef_cause',
                         EnvironmentalFactor.objects.only('id', 'name'))
        self.set_choices('ef_avoid',
                         EnvironmentalFactor.objects.only('id', 'name'))
        self.set_choices('housing_prefer',
                         HousingCategory.objects.only('id', 'name'))

    def save(self):
        self.instance.housing_completed = True
        instance = super(AttendeeHousingDataForm, self).save()
        if (self.instance.person == self.instance.event_person.person and
                self.cleaned_data['save_as_defaults']):
            person = self.instance.person
            person.ef_cause = instance.ef_cause.all()
            person.ef_avoid = instance.ef_avoid.all()
            person.person_prefer = instance.person_prefer
            person.person_avoid = instance.person_avoid
            person.housing_prefer = instance.housing_prefer.all()
            person.other_needs = instance.other_needs
            person.modified_directly = True
            person.save()
        return instance


class HousingSlotForm(forms.ModelForm):
    class Meta:
        model = HousingSlot
        fields = ('spaces', 'spaces_max')


class HostingForm(MemoModelForm):
    save_as_defaults = forms.BooleanField(initial=True)

    class Meta:
        model = EventHousing
        exclude = ('event', 'home', 'event_person')

    def __init__(self, *args, **kwargs):
        super(HostingForm, self).__init__({}, *args, **kwargs)

        if self.instance.pk is None:
            person = self.instance.event_person.person
            self.initial.update({
                'contact_name': person.name,
                'contact_email': person.email,
                'contact_phone': person.phone,
            })
            home = self.instance.home
            if home is not None:
                self.fields['ef_present_confirm'] = forms.BooleanField(
                    required=True,
                    error_messages={'required': CONFIRM_ERROR},
                    label="Is this still correct?",
                )
                self.fields['ef_avoid_confirm'] = forms.BooleanField(
                    required=True,
                    error_messages={'required': CONFIRM_ERROR},
                    label="Is this still correct?",
                )
                self.fields['housing_categories_confirm'] = forms.BooleanField(
                    required=True,
                    error_messages={'required': CONFIRM_ERROR},
                    label="Is this still correct?",
                )
                self.initial.update({
                    'address': home.address,
                    'city': home.city,
                    'state_or_province': home.state_or_province,
                    'country': home.country,
                    'public_transit_access': home.public_transit_access,
                    'ef_present': self.filter(EnvironmentalFactor.objects.only('id'),
                                              home_present=home),
                    'ef_avoid': self.filter(EnvironmentalFactor.objects.only('id'),
                                            home_avoid=home),
                    'person_prefer': home.person_prefer,
                    'person_avoid': home.person_avoid,
                    'housing_categories': self.filter(HousingCategory.objects.only('id'),
                                                      homes=home),
                })
        self.set_choices('ef_present',
                         EnvironmentalFactor.objects.only('id', 'name'))
        self.set_choices('ef_avoid',
                         EnvironmentalFactor.objects.only('id', 'name'))
        self.set_choices('housing_categories',
                         HousingCategory.objects.only('id', 'name'))

        self.nights = self.filter(Date, event_housing_dates=self.instance.event)
        slot_map = {}
        if self.instance.pk is not None:
            slot_map = {slot.night_id: slot
                        for slot in self.filter(HousingSlot, eventhousing=self.instance)}

        data = None if not self.is_bound else self.data
        self.slot_forms = []
        for night in self.nights:
            if night.pk in slot_map:
                instance = slot_map[night.pk]
            else:
                instance = HousingSlot(eventhousing=self.instance,
                                       night=night)

            self.slot_forms.append(HousingSlotForm(instance=instance,
                                                   data=data,
                                                   prefix='{}-{}'.format(self.prefix, night.pk)))

    def is_valid(self):
        valid = super(HostingForm, self).is_valid()
        if valid:
            for form in self.slot_forms:
                if not form.is_valid():
                    valid = False
                    break
        return valid

    def save(self):
        self.instance.is_completed = True
        instance = super(HostingForm, self).save()
        for form in self.slot_forms:
            form.instance.eventhousing = instance
            form.save()
        if self.cleaned_data['save_as_defaults']:
            home = instance.home or Home()
            new_home = home.pk is None
            home.address = instance.address
            home.city = instance.city
            home.state_or_province = instance.state_or_province
            home.country = instance.country
            home.public_transit_access = instance.public_transit_access
            home.save()
            home.ef_present = instance.ef_present.all()
            home.ef_avoid = instance.ef_avoid.all()
            home.person_prefer = instance.person_prefer
            home.person_avoid = instance.person_avoid
            home.housing_categories = instance.housing_categories.all()
            if new_home:
                instance.home = home
                instance.save()
                person = instance.event_person.person
                person.home = home
                person.save()
        return instance


class AddCardForm(forms.Form):
    token = forms.CharField(required=True,
                            error_messages={'required': "No token was provided. Please try again."})

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(AddCardForm, self).__init__(*args, **kwargs)

    def save(self):
        return self.save_card(self.user, self.cleaned_data['token'])

    def save_card(self, user, token):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        save_user = False
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                description=user.name,
                metadata={
                    'brambling_id': user.id
                },
            )
            user.stripe_customer_id = customer.id
            save_user = True
        else:
            customer = stripe.Customer.retrieve(user.stripe_customer_id)
        self.customer = customer
        # This could throw some errors.
        card = customer.cards.create(card=token)

        # Check the fingerprint. Save and redirect if there's no conflict.
        # Otherwise error time!
        creditcard, created = CreditCard.objects.get_or_create(
            person=user,
            fingerprint=card.fingerprint,
            defaults={
                'stripe_card_id': card.id,
                'exp_month': card.exp_month,
                'exp_year': card.exp_year,
                'last4': card.last4,
                'brand': card.type,
            }
        )
        if not created:
            # Use the saved card on our system; delete the new stripe card.
            card.delete()

        if user.default_card_id is None:
            user.default_card = creditcard
            save_user = True

        if save_user:
            user.save()
        return creditcard


class BasePaymentForm(forms.Form):
    def __init__(self, event_person, amount, *args, **kwargs):
        self.event_person = event_person
        self.amount = amount
        super(BasePaymentForm, self).__init__(*args, **kwargs)

    def charge(self, card_or_token, customer=None):
        if self.amount <= 0:
            return None
        stripe.api_key = settings.STRIPE_SECRET_KEY
        # Amount is number of smallest currency units.
        return stripe.Charge.create(
            amount=int(self.amount * 100),
            currency=self.event_person.event.currency,
            customer=customer,
            card=card_or_token,
        )

    def save_payment(self, charge, creditcard):
        payment = Payment.objects.create(event_person=self.event_person,
                                         amount=self.amount,
                                         stripe_charge_id=charge.id,
                                         card=creditcard)
        return payment


class OneTimePaymentForm(BasePaymentForm, AddCardForm):
    save_card = forms.BooleanField(required=False)

    def __init__(self, event_person, amount, user, *args, **kwargs):
        super(OneTimePaymentForm, self).__init__(
            event_person=event_person,
            amount=amount,
            user=user,
            *args, **kwargs
        )

    def save(self):
        if self.cleaned_data['save_card']:
            creditcard = self.save_card(self.user, self.cleaned_data['token'])
            charge = self.charge(creditcard.stripe_card_id,
                                 self.customer)
        else:
            charge = self.charge(self.cleaned_data['token'])
            creditcard = CreditCard.objects.create(
                stripe_card_id=charge.card.id,
                exp_month=charge.card.exp_month,
                exp_year=charge.card.exp_year,
                last4=charge.card.last4,
                brand=charge.card.type,
                fingerprint=charge.card.fingerprint
            )

        return self.save_payment(charge, creditcard)


class SavedCardPaymentForm(BasePaymentForm):
    card = forms.ModelChoiceField(CreditCard)

    def __init__(self, *args, **kwargs):
        super(SavedCardPaymentForm, self).__init__(*args, **kwargs)
        self.fields['card'].queryset = self.event_person.person.cards.all()
        self.fields['card'].initial = self.event_person.person.default_card

    def save(self):
        card = self.cleaned_data['card']
        charge = self.charge(card.stripe_card_id,
                             self.event_person.person.stripe_customer_id)
        return self.save_payment(charge, card)
