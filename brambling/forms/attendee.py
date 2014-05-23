from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.models import BaseModelFormSet
from django.utils import timezone
import floppyforms.__future__ as forms
import stripe
from zenaida.forms import MemoModelForm

from brambling.models import (Person, Discount, EventPerson, Date,
                              EventHousing, PersonItem, PersonDiscount,
                              EnvironmentalFactor, HousingCategory, CreditCard,
                              Payment, Home, HousingRequest, HousingSlot)


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


class EventPersonForm(forms.ModelForm):
    class Meta:
        model = EventPerson
        exclude = ('event', 'person', 'event_pass')

    def __init__(self, *args, **kwargs):
        super(EventPersonForm, self).__init__(*args, **kwargs)

        # You can't put someone else on the hook for hosting.
        if self.instance.event_pass.owner != self.instance.event_pass.buyer:
            self.fields['status'].choices = self.fields['status'].choices[:-1]

    def save(self):
        self.instance.is_completed = True
        return super(EventPersonForm, self).save()


class HousingRequestForm(MemoModelForm):
    class Meta:
        model = HousingRequest
        exclude = ('event', 'person')

    def __init__(self, eventperson, request, *args, **kwargs):
        self.eventperson = eventperson
        self.request = request
        super(HousingRequestForm, self).__init__(*args, **kwargs)

        for field in ('ef_cause_confirm', 'ef_avoid_confirm'):
            self.fields[field].required = True

        if self.instance.person == request.user:
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
        self.set_choices('nights', Date, event_housing_dates=self.instance.event)
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
        instance = super(HousingRequestForm, self).save()
        if (self.instance.person == self.request.user and
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


class EventHousingForm(MemoModelForm):
    save_as_defaults = forms.BooleanField(initial=True)

    class Meta:
        model = EventHousing
        exclude = ('event', 'home')

    def __init__(self, eventperson, request=None, *args, **kwargs):
        # We don't actually use request, but we want similarity to
        # HousingRequestForm.
        self.request = request
        self.eventperson = eventperson
        super(EventHousingForm, self).__init__(*args, **kwargs)
        for field in ('ef_present_confirm', 'ef_avoid_confirm', 'housing_categories_confirm'):
            self.fields[field].required = True

        if self.instance.pk is None:
            home = self.instance.home
            self.initial.update({
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
        slot_map = None
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
        valid = super(EventHousingForm, self).is_valid()
        if valid:
            for form in self.slot_forms:
                if not form.is_valid():
                    valid = False
                    break
        return valid

    def save(self):
        instance = super(EventHousingForm, self).save()
        for form in self.slot_forms:
            form.instance.eventhousing = instance
            form.save()
        if self.cleaned_data['save_as_defaults']:
            home = instance.home
            home.ef_present = instance.ef_present.all()
            home.ef_avoid = instance.ef_avoid.all()
            home.person_prefer = instance.person_prefer.all()
            home.person_avoid = instance.person_avoid.all()
            home.housing_categories = instance.housing_categories.all()
            home.save()
        return instance


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
                                         stripe_charge_id=charge.id,
                                         card=card)
        return payment
