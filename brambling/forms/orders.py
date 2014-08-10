from django.conf import settings
from django.db.models import Q
import floppyforms.__future__ as forms
import stripe
from zenaida.forms import MemoModelForm

from brambling.models import (Date, EventHousing, EnvironmentalFactor,
                              HousingCategory, CreditCard, Payment, Home,
                              Attendee, HousingSlot, BoughtItem, Item)


CONFIRM_ERROR = "Please check this box to confirm the value is correct"


class AttendeeBasicDataForm(forms.ModelForm):
    additional_items = forms.ModelMultipleChoiceField(BoughtItem, required=False)

    class Meta:
        model = Attendee
        exclude = ()

    def __init__(self, event_pass, *args, **kwargs):
        super(AttendeeBasicDataForm, self).__init__(*args, **kwargs)
        self.fields['liability_waiver'].required = True
        self.event_pass = event_pass
        self.order = event_pass.order
        additional_items = self.order.bought_items.filter(
            Q(attendee__isnull=True) | Q(attendee=event_pass.attendee_id)
        ).exclude(item_option__item__category=Item.PASS)
        if additional_items:
            self.fields['additional_items'].queryset = additional_items
            if self.instance.pk:
                self.fields['additional_items'].initial = self.order.bought_items.filter(
                    attendee=event_pass.attendee_id
                ).exclude(item_option__item__category=Item.PASS)
            else:
                self.fields['additional_items'].initial = additional_items
        else:
            del self.fields['additional_items']

    def save(self):
        self.instance.order = self.order
        self.instance.event_pass = self.event_pass
        self.instance.basic_completed = True
        instance = super(AttendeeBasicDataForm, self).save()
        if self.cleaned_data.get('additional_items'):
            self.cleaned_data['additional_items'].update(attendee=instance)
        self.event_pass.attendee = instance
        self.event_pass.save()
        return instance


class AttendeeHousingDataForm(MemoModelForm):
    class Meta:
        model = Attendee
        fields = ('nights', 'ef_cause', 'ef_avoid', 'person_prefer',
                  'person_avoid', 'housing_prefer', 'other_needs')

    def __init__(self, *args, **kwargs):
        super(AttendeeHousingDataForm, self).__init__(*args, **kwargs)

        if self.instance.person == self.instance.order.person:
            self.fields['save_as_defaults'] = forms.BooleanField(initial=True, required=False)

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
        self.set_choices('nights', Date, event_housing_dates=self.instance.order.event)
        self.set_choices('ef_cause',
                         EnvironmentalFactor.objects.only('id', 'name'))
        self.set_choices('ef_avoid',
                         EnvironmentalFactor.objects.only('id', 'name'))
        self.set_choices('housing_prefer',
                         HousingCategory.objects.only('id', 'name'))

    def save(self):
        self.instance.housing_completed = True
        instance = super(AttendeeHousingDataForm, self).save()
        if (self.instance.person == self.instance.order.person and
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
    save_as_defaults = forms.BooleanField(initial=True, required=False)

    class Meta:
        model = EventHousing
        exclude = ('event', 'home', 'order')

    def __init__(self, *args, **kwargs):
        super(HostingForm, self).__init__({}, *args, **kwargs)

        if self.instance.pk is None:
            person = self.instance.order.person
            self.initial.update({
                'contact_name': person.get_full_name(),
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
                person = instance.order.person
                person.home = home
                person.save()
        return instance


class AddCardForm(forms.Form):
    token = forms.CharField(required=True,
                            error_messages={'required': "No token was provided. Please try again."})

    def __init__(self, user, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.user = user
        super(AddCardForm, self).__init__(*args, **kwargs)

    def _post_clean(self):
        if 'token' in self.cleaned_data:
            token = self.cleaned_data['token']
            try:
                self.card = self.add_card(token)
            except stripe.error.CardError, e:
                self.add_error(None, e.message)

    def add_card(self, token):
        user = self.user
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                description=user.get_full_name(),
                metadata={
                    'brambling_id': user.id
                },
            )
            user.stripe_customer_id = customer.id
            user.save()
        else:
            customer = stripe.Customer.retrieve(user.stripe_customer_id)
        self.customer = customer
        return customer.cards.create(card=token)

    def save(self):
        return self.save_card(self.card, self.user)

    def save_card(self, card, user):
        creditcard = CreditCard.objects.create(
            person=self.user,
            fingerprint=card.fingerprint,
            stripe_card_id=card.id,
            exp_month=card.exp_month,
            exp_year=card.exp_year,
            last4=card.last4,
            brand=card.type,
        )

        if user and user.default_card_id is None:
            user.default_card = creditcard
            user.save()

        return creditcard


class BasePaymentForm(forms.Form):
    def __init__(self, order, amount, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.order = order
        self.amount = amount
        super(BasePaymentForm, self).__init__(*args, **kwargs)

    def charge(self, card_or_token, customer=None):
        if self.amount <= 0:
            return None
        # Amount is number of smallest currency units.
        return stripe.Charge.create(
            amount=int(self.amount * 100),
            currency=self.order.event.currency,
            customer=customer,
            card=card_or_token,
        )

    def save_payment(self, charge, creditcard):
        payment = Payment.objects.create(order=self.order,
                                         amount=self.amount,
                                         method=Payment.STRIPE,
                                         remote_id=charge.id,
                                         card=creditcard)
        return payment


class OneTimePaymentForm(BasePaymentForm, AddCardForm):
    save_card = forms.BooleanField(required=False)

    def __init__(self, order, amount, user, *args, **kwargs):
        super(OneTimePaymentForm, self).__init__(
            order=order,
            amount=amount,
            user=user,
            *args, **kwargs
        )

    def _post_clean(self):
        try:
            if self.cleaned_data['save_card']:
                self.card = self.add_card(self.cleaned_data['token'])
                self._charge = self.charge(self.card.id, self.customer)
            else:
                self._charge = self.charge(self.cleaned_data['token'])
                self.card = self._charge.card
        except stripe.error.CardError, e:
            self.add_error(None, e.message)

    def save(self):
        if self.cleaned_data['save_card']:
            user = self.user
        else:
            user = None
        creditcard = self.save_card(self.card, user)
        return self.save_payment(self._charge, creditcard)


class SavedCardPaymentForm(BasePaymentForm):
    card = forms.ModelChoiceField(CreditCard)

    def __init__(self, *args, **kwargs):
        super(SavedCardPaymentForm, self).__init__(*args, **kwargs)
        self.fields['card'].queryset = self.order.person.cards.all()
        self.fields['card'].initial = self.order.person.default_card

    def _post_clean(self):
        self.card = self.cleaned_data['card']
        try:
            self._charge = self.charge(self.card.stripe_card_id,
                                       self.order.person.stripe_customer_id)
        except stripe.error.CardError, e:
            self.add_error(None, e.message)

    def save(self):
        return self.save_payment(self._charge, self.card)
