import datetime
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.models import construct_instance
from django.utils import timezone
from zenaida import forms

from brambling.models import (Person, Home, Item, Discount,
                              EventPerson, Date, EventHousing, PersonItem,
                              PersonDiscount, EnvironmentalFactor,
                              HousingCategory, CreditCard)


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


class ReservationForm(forms.ModelForm):
    """Lets a person choose item options to buy."""
    option_id = forms.IntegerField()

    class Meta:
        model = PersonItem
        fields = ()

    def __init__(self, buyer, item_option, *args, **kwargs):
        super(ReservationForm, self).__init__(*args, **kwargs)
        self.buyer = buyer
        self.item_option = item_option
        self.fields['option_id'].initial = item_option.id

    def clean(self):
        cleaned_data = super(ReservationForm, self).clean()
        if self.item_option.id != cleaned_data.get('option_id'):
            raise ValidationError("Be sure not to fiddle with the HTML code.")
        return cleaned_data

    def _post_clean(self):
        super(ReservationForm, self)._post_clean()
        self.instance.buyer = self.buyer
        self.instance.item_option = self.item_option
        self.instance.owner = None
        self.instance.status = PersonItem.RESERVED


class PersonItemForm(forms.MemoModelForm):
    """
    If you bought it, you can change the owner.

    If you own it, you can set up hosting.

    So there are three sets of forms needed:

    1. set of forms for the person who owns the item. If this is the current
       user, include host form.

    2. if that isn't the buyer, and the buyer is the current user, a set of
       blank forms for the person who bought the item.

    3. If the current user is the buyer, a set of blank forms for non-owner
       people who it might be transferred to.

    ... all of which is only available if housing data is even being collected.

    """
    class Meta:
        model = PersonItem
        fields = ('owner',)

    def __init__(self, event, memo_dict, user, data=None, files=None,
                 *args, **kwargs):
        self.event = event
        self.user = user
        super(PersonItemForm, self).__init__(memo_dict, data, files,
                                             *args, **kwargs)
        self.buyer_id = self.instance.buyer_id
        self.owner_id = self.instance.owner_id

        if self.buyer_id != user.id:
            del self.fields['owner']
        else:
            self.initial['owner'] = self.owner_id or self.buyer_id

        self.set_choices('owner', Person.objects.only('id', 'name'))

        self.item = self.instance.item_option.item
        #self.get(Item, options__personitem=self.instance)
        if event.collect_housing_data and self.item.category == Item.PASS:
            base_person_qs = Person.objects.prefetch_related(
                'ef_cause', 'ef_avoid', 'person_prefer', 'person_avoid',
                'housing_prefer',
            )
            try:
                self.owner = self.get(base_person_qs, id=self.owner_id)
            except Person.DoesNotExist:
                self.owner = None
            self.instance.owner = self.owner
            eventperson_kwargs = {
                'user': self.user,
                'event': self.event,
                'memo_dict': memo_dict,
                'personitem': self.instance,
                'data': data,
                'files': files
            }
            housing_kwargs = {
                'event': self.event,
                'memo_dict': memo_dict,
                'data': data,
                'files': files
            }
            self.owner_forms = {
                'eventperson': EventPersonForm(
                    person=self.owner,
                    prefix=self.prefix + '-owner-eventperson',
                    **eventperson_kwargs
                ),
                'guest': GuestForm(
                    person=self.owner,
                    with_defaults=False,
                    personitem=self.instance,
                    prefix=self.prefix + '-owner-guest',
                    **housing_kwargs
                )
            }
            if self.user == self.owner:
                self.owner_forms['host'] = HostingForm(
                    home=self.get(Home.objects.prefetch_related(
                        'ef_present', 'ef_avoid', 'person_prefer',
                        'person_avoid', 'housing_categories'
                    ), id=self.owner.home_id),
                    prefix=self.prefix + '-owner-host',
                    **housing_kwargs
                )

            if self.user.id == self.buyer_id:
                if self.buyer_id != self.owner_id:
                    self.buyer = self.get(base_person_qs, id=self.buyer_id)
                    self.instance.buyer = self.buyer
                    self.buyer_forms = {
                        'eventperson': EventPersonForm(
                            person=self.buyer,
                            prefix=self.prefix + '-buyer-eventperson',
                            **eventperson_kwargs
                        ),
                        'guest': GuestForm(
                            person=self.buyer,
                            with_defaults=True,
                            personitem=self.instance,
                            prefix=self.prefix + '-buyer-guest',
                            **housing_kwargs
                        ),
                        'host': HostingForm(
                            home=self.get(Home, id=self.buyer.home_id),
                            prefix=self.prefix + '-buyer-host',
                            **housing_kwargs
                        )
                    }
                self.empty_forms = {
                    'eventperson': EventPersonForm(
                        person=None,
                        prefix=self.prefix + '-empty-eventperson',
                        **eventperson_kwargs
                    ),
                    'guest': GuestForm(
                        person=None,
                        personitem=self.instance,
                        prefix=self.prefix + '-empty-guest',
                        **housing_kwargs
                    ),
                }

    def has_changed(self):
        changed = super(PersonItemForm, self).has_changed()
        if (not changed and self.event.collect_housing_data and
                self.item.category == Item.PASS):
            # Use owner forms if the owner hasn't changed.
            # If it has changed, check if the new owner is the buyer
            # or a new person and use the buyer forms or empty forms
            # respectively.
            if not 'owner' in self.changed_data:
                # Owner forms.
                changed = any((form.has_changed()
                               for form in self.owner_forms.values()))
            elif self.cleaned_data['owner'] == self.buyer:
                # Buyer forms
                changed = any((form.has_changed()
                               for form in self.buyer_forms.values()))
            else:
                # Empty forms.
                changed = any((form.has_changed()
                               for form in self.empty_forms.values()))
        return changed

    def is_valid(self):
        valid = super(PersonItemForm, self).is_valid()
        if (valid and self.event.collect_housing_data and
                self.item.category == Item.PASS):
            # Use owner forms if the owner hasn't changed.
            # If it has changed, check if the new owner is the buyer
            # or a new person and use the buyer forms or empty forms
            # respectively.
            if not 'owner' in self.changed_data:
                # Owner forms.
                valid = self.is_valid_group(self.owner_forms)
            elif self.cleaned_data['owner'] == self.buyer:
                # Buyer forms
                valid = self.is_valid_group(self.buyer_forms)
            else:
                # Empty forms.
                valid = self.is_valid_group(self.empty_forms)
        return valid

    def is_valid_group(self, form_group):
        epf = form_group['eventperson']
        valid = epf.is_valid()
        if valid:
            housing = epf.cleaned_data['housing']
            if housing == EventPerson.NEED:
                valid = form_group['guest'].is_valid()
            elif housing == EventPerson.HOST:
                valid = form_group['host'].is_valid()
        return valid

    def save(self, commit=True):
        instance = super(PersonItemForm, self).save()
        if (self.event.collect_housing_data and
                self.item.category == Item.PASS):
            # Use owner forms if the owner hasn't changed.
            # If it has changed, check if the new owner is the buyer
            # or a new person and use the buyer forms or empty forms
            # respectively.
            if not 'owner' in self.changed_data:
                # Owner forms.
                self.save_group(self.owner_forms)
            else:
                eventperson = self.owner_forms['eventperson'].instance
                if eventperson.pk:
                    eventperson.delete()
                if self.cleaned_data['owner'] == self.buyer:
                    # Buyer forms
                    self.save_group(self.buyer_forms)
                else:
                    # Empty forms.
                    self.save_group(self.empty_forms)
        return instance

    def save_group(self, form_group):
        eventperson = form_group['eventperson'].instance
        eventperson.person = self.instance.owner
        eventperson.event_pass = self.instance
        housing = form_group['eventperson'].cleaned_data['housing']
        if housing == EventPerson.NEED:
            opts = form_group['guest']._meta
            eventperson = construct_instance(form_group['guest'], eventperson,
                                             opts.fields, opts.exclude)
        elif housing == EventPerson.HOST:
            form_group['host'].save()
        eventperson.save()

    def clean_owner(self):
        # Enforce max_per_owner
        owner = self.cleaned_data['owner']
        max_per_owner = self.instance.item_option.max_per_owner
        if 'owner' in self.changed_data and max_per_owner is not None:
            reservation_start = (
                timezone.now() -
                datetime.timedelta(minutes=self.event.reservation_timeout)
            )
            # Clear any old PersonItems. And any old registrations with them.
            PersonItem.objects.filter(status=PersonItem.RESERVED,
                                      item_option__item__event=self.event,
                                      owner=owner,
                                      added__lt=reservation_start).delete()
            count = PersonItem.objects.filter(item_option__item__event=self.event,
                                              owner=owner).count()
            if count >= max_per_owner:
                raise ValidationError("{} cannot own any more of these."
                                      "".format(unicode(owner)))
        return owner


class PersonItemFormSet(forms.models.BaseModelFormSet):
    def __init__(self, event, user, *args, **kwargs):
        self.event = event
        self.user = user
        self.memo_dict = {}
        super(PersonItemFormSet, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs.update({
            'event': self.event,
            'memo_dict': self.memo_dict,
            'user': self.user,
        })
        return super(PersonItemFormSet, self)._construct_form(i, **kwargs)


class EventPersonForm(forms.MemoModelForm):
    class Meta:
        model = EventPerson
        fields = ('car_spaces', 'bedtime', 'wakeup', 'housing')

    def __init__(self, person, user, personitem, event, memo_dict,
                 *args, **kwargs):
        self.person = person
        self.event = event
        self.personitem = personitem
        self.memo_dict = memo_dict
        if person is None:
            instance = EventPerson(event=event)
        else:
            instance = EventPerson(person=person, event=event)
            try:
                self.get(EventPerson, person=person, event=event,
                         event_pass=personitem)
            except EventPerson.DoesNotExist:
                pass
        kwargs['instance'] = instance
        super(EventPersonForm, self).__init__(memo_dict, *args, **kwargs)
        if person != user:
            self.fields['housing'].choices = self.fields['housing'].choices[:-1]


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

    def __init__(self, person, personitem, event, memo_dict,
                 with_defaults=True, *args, **kwargs):
        self.person = person
        self.personitem = personitem
        self.event = event
        self.memo_dict = memo_dict
        self.with_defaults = with_defaults
        if person is None:
            instance = EventPerson(event=event)
        else:
            instance = EventPerson(person=person, event=event)
            try:
                instance = self.get(EventPerson,
                                    person=person,
                                    event=event,
                                    event_pass=personitem)
            except EventPerson.DoesNotExist:
                pass
        kwargs['instance'] = instance
        super(GuestForm, self).__init__(memo_dict, *args, **kwargs)
        if with_defaults and person is not None:
            self.fields['save_as_defaults'] = forms.BooleanField(initial=True)
            if self.instance.pk is None:
                self.initial.update({
                    'ef_cause': person.ef_cause.all(),
                    'ef_avoid': person.ef_avoid.all(),
                    'person_prefer': person.person_prefer.all(),
                    'person_avoid': person.person_avoid.all(),
                    'housing_prefer': person.housing_prefer.all(),
                    'other_needs': person.other_needs,
                })
                self.instance.event = event
                self.instance.person = person
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
        if self.with_defaults and self.cleaned_data['save_as_defaults']:
            self.owner.ef_cause = instance.ef_cause.all()
            self.owner.ef_avoid = instance.ef_avoid.all()
            self.owner.person_prefer = instance.person_prefer.all()
            self.owner.person_avoid = instance.person_avoid.all()
            self.owner.housing_prefer = instance.housing_prefer.all()
            self.owner.other_needs = instance.other_needs
            self.owner.save()
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

    def __init__(self, person, *args, **kwargs):
        super(CheckoutForm, self).__init__(*args, **kwargs)
        self.person = person
        self.fields['card'].queryset = person.cards.all()
        self.fields['card'].initial = person.default_card

    def save(self):
        pass
