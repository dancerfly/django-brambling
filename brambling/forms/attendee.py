from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
import floppyforms.__future__ as forms
import stripe
from zenaida.forms import MemoModelForm

from brambling.models import (Person, Discount, EventPerson, Date,
                              EventHousing, UsedDiscount,
                              EnvironmentalFactor, HousingCategory, CreditCard,
                              Payment, Home, Attendee, HousingSlot)


CONFIRM_ERROR = "Please check this box to confirm the value is correct"


class UsedDiscountForm(forms.ModelForm):
    discount = forms.CharField(max_length=20, label="discount code")

    class Meta:
        fields = ()
        model = UsedDiscount

    def __init__(self, event, person, *args, **kwargs):
        self.event = event
        self.person = person
        self.event_person = EventPerson.objects.get_cached(event, person)
        super(UsedDiscountForm, self).__init__(*args, **kwargs)

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
        self.instance.event_person = self.event_person
        if 'discount' in self.cleaned_data:
            self.instance.discount = self.cleaned_data['discount']
        super(UsedDiscountForm, self)._post_clean()


class AttendeeBasicDataForm(forms.ModelForm):
    class Meta:
        model = Attendee

    def __init__(self, *args, **kwargs):
        super(AttendeeBasicDataForm, self).__init__(*args, **kwargs)
        self.fields['liability_waiver'].required = True


class AttendeeHousingDataForm(MemoModelForm):
    class Meta:
        model = Attendee
        fields = ('nights', 'ef_cause', 'ef_cause_confirm', 'ef_avoid',
                  'ef_avoid_confirm', 'person_prefer', 'person_avoid',
                  'housing_prefer', 'other_needs')

    def __init__(self, *args, **kwargs):
        super(AttendeeHousingDataForm, self).__init__(*args, **kwargs)
        self.fields['ef_cause_confirm'].error_messages['required'] = CONFIRM_ERROR
        self.fields['ef_avoid_confirm'].error_messages['required'] = CONFIRM_ERROR

        for field in ('ef_cause_confirm', 'ef_avoid_confirm'):
            self.fields[field].required = True

        if self.instance.person == self.instance.event_person.person:
            self.fields['save_as_defaults'] = forms.BooleanField(initial=True)
            if self.instance.pk is None:
                owner = self.instance.person
                self.initial.update({
                    'ef_cause': self.filter(EnvironmentalFactor.objects.only('id'),
                                            person_cause=owner),
                    'ef_avoid': self.filter(EnvironmentalFactor.objects.only('id'),
                                            person_avoid=owner),
                    'person_prefer': self.filter(Person.objects.only('id'),
                                                 preferred_by=owner),
                    'person_avoid': self.filter(Person.objects.only('id'),
                                                avoided_by=owner),
                    'housing_prefer': self.filter(HousingCategory.objects.only('id'),
                                                  preferred_by=owner),
                    'other_needs': owner.other_needs,
                })
        self.fields['nights'].required = True
        self.set_choices('nights', Date, event_housing_dates=self.instance.event_person.event)
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
        self.instance.housing_completed = True
        instance = super(AttendeeHousingDataForm, self).save()
        if (self.instance.person == self.instance.event_person.person and
                self.cleaned_data['save_as_defaults']):
            person = self.instance.person
            person.ef_cause = instance.ef_cause.all()
            person.ef_avoid = instance.ef_avoid.all()
            person.person_prefer = instance.person_prefer.all()
            person.person_avoid = instance.person_avoid.all()
            person.housing_prefer = instance.housing_prefer.all()
            person.other_needs = instance.other_needs
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
        for field in ('ef_present_confirm', 'ef_avoid_confirm', 'housing_categories_confirm'):
            self.fields[field].required = True
            self.fields[field].error_messages['required'] = CONFIRM_ERROR

        if self.instance.pk is None:
            person = self.instance.event_person.person
            self.initial.update({
                'contact_name': person.name,
                'contact_email': person.email,
                'contact_phone': person.phone,
            })
            home = self.instance.home
            if home is not None:
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
                    'person_prefer': self.filter(Person.objects.only('id'),
                                                 preferred_by_homes=home),
                    'person_avoid': self.filter(Person.objects.only('id'),
                                                avoided_by_homes=home),
                    'housing_categories': self.filter(HousingCategory.objects.only('id'),
                                                      homes=home),
                })
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
            home.ef_present = instance.ef_present.all()
            home.ef_avoid = instance.ef_avoid.all()
            home.person_prefer = instance.person_prefer.all()
            home.person_avoid = instance.person_avoid.all()
            home.housing_categories = instance.housing_categories.all()
            home.save()
            if new_home:
                instance.home = home
                instance.save()
                person = instance.event_person.person
                person.home = home
        return instance


class CheckoutForm(forms.Form):
    card = forms.ModelChoiceField(CreditCard)

    def __init__(self, event, person, balance, *args, **kwargs):
        super(CheckoutForm, self).__init__(*args, **kwargs)
        self.person = person
        self.event = event
        self.event_person = EventPerson.objects.get_cached(self.event, self.person)
        self.balance = balance
        self.fields['card'].queryset = person.cards.all()
        self.fields['card'].initial = person.default_card

        if self.balance <= 0:
            del self.fields['card']

    def clean(self):
        cleaned_data = super(CheckoutForm, self).clean()
        if not self.event_person.cart_is_valid():
            raise ValidationError("Cart must be ready for checkout before paying.", self.event_person.cart_errors)
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
        payment = Payment.objects.create(event_person=self.event_person,
                                         amount=self.balance,
                                         stripe_charge_id=charge.id,
                                         card=card)
        return payment
