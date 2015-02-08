from django.db.models import Q
import floppyforms.__future__ as forms
import stripe
from zenaida.forms import MemoModelForm

from brambling.models import (Date, EventHousing, EnvironmentalFactor,
                              HousingCategory, CreditCard, Transaction, Home,
                              Attendee, HousingSlot, BoughtItem, Item,
                              Order, Event)
from brambling.utils.payment import (dwolla_charge, stripe_prep, stripe_charge)

from localflavor.us.forms import USZipCodeField


CONFIRM_ERROR = "Please check this box to confirm the value is correct"


class AttendeeBasicDataForm(forms.ModelForm):
    additional_items = forms.ModelMultipleChoiceField(BoughtItem, required=False)

    class Meta:
        model = Attendee
        exclude = ()
        widgets = {
            'housing_status': forms.RadioSelect,
        }

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

        if 'housing_status' in self.fields:
            self.fields['housing_status'].label = "Housing"
            self.fields['housing_status'].choices = (
                (Attendee.NEED, 'Request housing'),
                (Attendee.HAVE, 'Already arranged'),
                (Attendee.HOME, 'Staying at own home'),
            )
            self.fields['housing_status'].initial = ''
            self.fields['phone'].help_text = 'Required if requesting housing'

    def clean_housing_status(self):
        housing_status = self.cleaned_data['housing_status']
        if housing_status == Attendee.NEED and not self.cleaned_data['phone']:
            self.add_error('phone', 'Phone number is required to request housing.')
        return housing_status

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

        if self.instance.person and self.instance.person == self.instance.order.person:
            self.fields['save_as_defaults'] = forms.BooleanField(initial=True, required=False)

            if self.instance.person and not self.instance.housing_completed:
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
        self.initial['nights'] = self.fields['nights'].queryset
        self.set_choices('ef_cause',
                         EnvironmentalFactor.objects.only('id', 'name'))
        self.set_choices('ef_avoid',
                         EnvironmentalFactor.objects.only('id', 'name'))
        self.set_choices('housing_prefer',
                         HousingCategory.objects.only('id', 'name'))

    def save(self):
        self.instance.housing_completed = True
        instance = super(AttendeeHousingDataForm, self).save()
        if (self.instance.person and
                self.instance.person == self.instance.order.person and
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


class SurveyDataForm(forms.ModelForm):
    send_flyers_zip = USZipCodeField(label="Zip code", widget=forms.TextInput, required=False)

    class Meta:
        model = Order
        fields = (
            'heard_through', 'heard_through_other', 'send_flyers',
            'send_flyers_address', 'send_flyers_address_2', 'send_flyers_city',
            'send_flyers_state_or_province', 'send_flyers_zip',
            'send_flyers_country',
        )
        widgets = {
            'send_flyers_country': forms.Select
        }

    def clean_send_flyers(self):
        send_flyers = self.cleaned_data['send_flyers']
        if send_flyers:
            self.fields['send_flyers_address'].required = True
            self.fields['send_flyers_city'].required = True
            self.fields['send_flyers_state_or_province'].required = True
            self.fields['send_flyers_country'].required = True
            self.fields['send_flyers_zip'].required = True
        return send_flyers


class HousingSlotForm(forms.ModelForm):
    def clean_spaces_max(self):
        cd = self.cleaned_data
        spaces = cd.get('spaces')
        spaces_max = cd.get('spaces_max')
        if not spaces_max >= spaces:
            raise forms.ValidationError("Max spaces must be greater than or equal to comfy spaces.")
        return spaces_max

    class Meta:
        model = HousingSlot
        fields = ('spaces', 'spaces_max')


class HostingForm(MemoModelForm):
    providing_housing = forms.BooleanField(initial=False, required=False)
    save_as_defaults = forms.BooleanField(initial=True, required=False,
            label="Remember this information for future events.",
            help_text="You will still be able to modify it later.")
    zip_code = USZipCodeField(widget=forms.TextInput)

    class Meta:
        model = EventHousing
        exclude = ('event', 'home', 'order')
        widgets = {
            'country': forms.Select
        }

    def __init__(self, *args, **kwargs):
        super(HostingForm, self).__init__({}, *args, **kwargs)

        self.initial.update({
            'providing_housing': self.instance.order.providing_housing
        })
        person = self.instance.order.person
        if person is None:
            del self.fields['save_as_defaults']

        if self.instance.pk is None:
            if person is not None:
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
                    'address_2': home.address_2,
                    'city': home.city,
                    'state_or_province': home.state_or_province,
                    'zip_code': home.zip_code,
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
        if not self.cleaned_data['providing_housing']:
            return True
        any_slots = False
        for form in self.slot_forms:
            if not form.is_valid():
                valid = False
                # Otherwise invalid forms would cause "at least one space"
                # errors.
                any_slots = True
            elif form.cleaned_data['spaces'] or form.cleaned_data['spaces_max']:
                any_slots = True
        if not any_slots:
            self.add_error(None, "At least one space must be provided to offer housing.")
            valid = False
        return valid

    def save(self):
        if self.cleaned_data['providing_housing']:
            self.instance.order.providing_housing = True
            self.instance.order.save()

            self.instance.is_completed = True
            instance = super(HostingForm, self).save()
            for form in self.slot_forms:
                form.instance.eventhousing = instance
                form.save()
            if self.cleaned_data.get('save_as_defaults'):
                home = instance.home or Home()
                new_home = home.pk is None
                home.address = instance.address
                home.address_2 = instance.address_2
                home.city = instance.city
                home.state_or_province = instance.state_or_province
                home.zip_code = instance.zip_code
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
        else:
            self.instance.order.providing_housing = False
            self.instance.order.save()
            if self.instance.pk:
                self.instance.delete()
            return self.instance


class AddCardForm(forms.Form):
    token = forms.CharField(required=True,
                            error_messages={'required': "No token was provided. Please try again."})
    api_type = Event.LIVE

    def __init__(self, user, *args, **kwargs):
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
        stripe_prep(self.api_type)

        if self.api_type == Event.LIVE:
            customer_attr = 'stripe_customer_id'
        else:
            customer_attr = 'stripe_test_customer_id'
        customer_id = getattr(user, customer_attr)

        if not customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                description=user.get_full_name(),
                metadata={
                    'brambling_id': user.id
                },
            )
            setattr(user, customer_attr, customer.id)
            user.save()
        else:
            customer = stripe.Customer.retrieve(customer_id)
        self.customer = customer
        return customer.cards.create(card=token)

    def save(self):
        return self.save_card(self.card, self.user)

    def save_card(self, card, user):
        creditcard = CreditCard.objects.create(
            person=user,
            fingerprint=card.fingerprint,
            stripe_card_id=card.id,
            exp_month=card.exp_month,
            exp_year=card.exp_year,
            last4=card.last4,
            brand=card.brand,
            api_type=self.api_type
        )

        if user and user.default_card_id is None:
            user.default_card = creditcard
            user.save()

        return creditcard


class BasePaymentForm(forms.Form):
    def __init__(self, order, amount, *args, **kwargs):
        self.api_type = order.event.api_type
        self.order = order
        self.amount = amount
        super(BasePaymentForm, self).__init__(*args, **kwargs)

    def save_payment(self, charge, creditcard):
        return Transaction.from_stripe_charge(
            charge,
            card=creditcard,
            api_type=self.api_type,
            order=self.order,
            event=self.order.event)


class OneTimePaymentForm(BasePaymentForm, AddCardForm):
    save_card = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(OneTimePaymentForm, self).__init__(*args, **kwargs)
        if not self.user.is_authenticated():
            del self.fields['save_card']

    def _post_clean(self):
        kwargs = {
            'amount': self.amount,
            'event': self.order.event,
        }
        try:
            if self.cleaned_data.get('save_card'):
                self.card = self.add_card(self.cleaned_data['token'])
                self._charge = stripe_charge(self.card.id, customer=self.customer, **kwargs)
            else:
                self._charge = stripe_charge(self.cleaned_data['token'], **kwargs)
                self.card = self._charge.card
        except stripe.error.CardError, e:
            self.add_error(None, e.message)

    def save(self):
        if self.cleaned_data.get('save_card'):
            user = self.user
        else:
            user = None
        creditcard = self.save_card(self.card, user)
        return self.save_payment(self._charge, creditcard)


class SavedCardPaymentForm(BasePaymentForm):
    card = forms.ModelChoiceField(CreditCard)

    def __init__(self, *args, **kwargs):
        super(SavedCardPaymentForm, self).__init__(*args, **kwargs)
        self.fields['card'].queryset = self.order.person.cards.filter(
            api_type=self.api_type)
        self.fields['card'].initial = self.order.person.default_card

    def _post_clean(self):
        self.card = self.cleaned_data['card']
        if self.api_type == Event.LIVE:
            customer_id = self.order.person.stripe_customer_id
        else:
            customer_id = self.order.person.stripe_test_customer_id
        try:
            self._charge = stripe_charge(
                self.card.stripe_card_id,
                amount=self.amount,
                event=self.order.event,
                customer=customer_id
            )
        except stripe.error.CardError, e:
            self.add_error(None, e.message)

    def save(self):
        return self.save_payment(self._charge, self.card)


class DwollaPaymentForm(BasePaymentForm):
    dwolla_pin = forms.RegexField(min_length=4, max_length=4, regex="\d+")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(DwollaPaymentForm, self).__init__(*args, **kwargs)

    def _post_clean(self):
        if 'dwolla_pin' in self.cleaned_data:
            self._charge = None
            if self.amount > 0:
                try:
                    self._charge = dwolla_charge(
                        user_or_order=self.user if self.user.is_authenticated() else self.order,
                        amount=float(self.amount),
                        event=self.order.event,
                        pin=self.cleaned_data['dwolla_pin']
                    )
                except Exception as e:
                    self.add_error(None, e.message)

    def save(self):
        return Transaction.from_dwolla_charge(
            self._charge,
            api_type=self.api_type,
            order=self.order,
            event=self.order.event)


class CheckPaymentForm(BasePaymentForm):
    def save(self):
        return Transaction.objects.create(
            transaction_type=Transaction.PURCHASE,
            order=self.order,
            amount=self.amount,
            method=Transaction.CHECK,
            is_confirmed=False,
            api_type=self.api_type,
            event=self.order.event
        )
