from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db.models import Q
from django.utils.crypto import get_random_string
import floppyforms.__future__ as forms

from brambling.models import (Attendee, Event, Item, ItemOption, Discount,
                              ItemImage, Transaction, Invite, CustomForm,
                              CustomFormField, Order, Organization, SavedReport)
from brambling.utils.international import clean_postal_code
from brambling.utils.payment import LIVE, TEST

from zenaida.forms import (GroupedModelMultipleChoiceField,
                           GroupedModelChoiceField)


class OrganizationProfileForm(forms.ModelForm):
    def __init__(self, request, *args, **kwargs):
        super(OrganizationProfileForm, self).__init__(*args, **kwargs)
        if self.instance.is_demo():
            del self.fields['slug']

    class Meta:
        widgets = {
            'country': forms.Select,
        }
        model = Organization
        fields = (
            'name', 'slug', 'description', 'website_url',
            'facebook_url', 'banner_image', 'city',
            'state_or_province', 'country', 'dance_styles'
        )


class OrganizationPermissionForm(forms.Form):
    editors = forms.CharField(help_text='Comma-separated email addresses. Each person will be sent an invitation to join the event as an editor.',
                              widget=forms.Textarea,
                              required=False)

    def __init__(self, request, instance, *args, **kwargs):
        super(OrganizationPermissionForm, self).__init__(*args, **kwargs)
        self.instance = instance
        self.request = request
        if self.instance.pk is None:
            self.instance.owner = request.user
        if not request.user == self.instance.owner:
            del self.fields['editors']

    def clean_editors(self):
        editors = self.cleaned_data['editors']
        if not editors:
            return []

        validator = EmailValidator()
        # Split email list by commas and trim whitespace:
        editors = [x.strip() for x in editors.split(',')]
        for editor in editors:
            validator(editor)
        return editors

    def save(self):
        if self.request.user == self.instance.owner and self.cleaned_data['editors']:
            for editor in self.cleaned_data['editors']:
                invite, created = Invite.objects.get_or_create_invite(
                    email=editor,
                    user=self.request.user,
                    kind=Invite.ORGANIZATION_EDITOR,
                    content_id=self.instance.pk
                )
                if created:
                    invite.send(
                        content=self.instance,
                        secure=self.request.is_secure(),
                        site=get_current_site(self.request),
                    )
        return self.instance


class OrganizationPaymentForm(forms.ModelForm):
    disconnect_stripe_live = forms.BooleanField(required=False)
    disconnect_stripe_test = forms.BooleanField(required=False)
    disconnect_dwolla_live = forms.BooleanField(required=False)
    disconnect_dwolla_test = forms.BooleanField(required=False)

    class Meta:
        model = Organization
        fields = (
            'check_payment_allowed', 'check_payable_to', 'check_recipient',
            'check_address', 'check_address_2', 'check_city',
            'check_state_or_province', 'check_zip', 'check_country',
        )
        widgets = {
            'check_country': forms.Select,
        }

    def __init__(self, request, *args, **kwargs):
        super(OrganizationPaymentForm, self).__init__(*args, **kwargs)
        if not self.instance.stripe_live_connected():
            del self.fields['disconnect_stripe_live']
        if not self.instance.stripe_test_connected():
            del self.fields['disconnect_stripe_test']
        if not self.instance.dwolla_live_connected():
            del self.fields['disconnect_dwolla_live']
        if not self.instance.dwolla_test_connected():
            del self.fields['disconnect_dwolla_test']
        self.request = request
        if self.instance.pk is None:
            self.instance.owner = request.user

    def clean_check_payment_allowed(self):
        cpa = self.cleaned_data['check_payment_allowed']
        if cpa:
            for field in ('check_payable_to', 'check_recipient',
                          'check_address', 'check_city', 'check_zip',
                          'check_state_or_province', 'check_country'):
                self.fields[field].required = True
        return cpa

    def clean(self):
        cleaned_data = super(OrganizationPaymentForm, self).clean()
        if 'check_zip' in cleaned_data:
            country = self.instance.check_country
            code = cleaned_data['check_zip']
            try:
                cleaned_data['check_zip'] = clean_postal_code(country, code)
            except ValidationError, e:
                del cleaned_data['check_zip']
                self.add_error('check_zip', e)
        return cleaned_data

    def has_check_errors(self):
        return any((f in self.errors
                    for f in self.fields
                    if f[:6] == ('check_')))

    def save(self):
        if self.cleaned_data.get('disconnect_stripe_live'):
            self.instance.stripe_user_id = ''
            self.instance.stripe_access_token = ''
            self.instance.stripe_refresh_token = ''
            self.instance.stripe_publishable_key = ''
        if self.cleaned_data.get('disconnect_stripe_test'):
            self.instance.stripe_test_user_id = ''
            self.instance.stripe_test_access_token = ''
            self.instance.stripe_test_refresh_token = ''
            self.instance.stripe_test_publishable_key = ''
        if self.cleaned_data.get('disconnect_dwolla_live'):
            self.instance.clear_dwolla_data(LIVE)
        if self.cleaned_data.get('disconnect_dwolla_test'):
            self.instance.clear_dwolla_data(TEST)
        return super(OrganizationPaymentForm, self).save()


class EventCreateForm(forms.ModelForm):
    template_event = forms.ModelChoiceField(queryset=Event.objects.all(), required=False)

    class Meta:
        model = Event
        fields = ('name', 'slug', 'start_date', 'end_date', 'start_time',
                  'end_time', 'organization', 'template_event')

    def __init__(self, request, *args, **kwargs):
        super(EventCreateForm, self).__init__(*args, **kwargs)
        self.request = request
        if not request.user.is_authenticated():
            raise ValueError("EventCreateForm requires an authenticated user.")
        self.fields['template_event'].queryset = Event.objects.filter(
            Q(organization__owner=request.user) |
            Q(organization__editors=request.user)
        ).order_by('-last_modified').distinct()
        self.fields['organization'].queryset = Organization.objects.filter(
            Q(owner=request.user) |
            Q(editors=request.user)
        ).order_by('name').distinct()

    def clean(self):
        cd = super(EventCreateForm, self).clean()
        if ('start_date' in cd and 'end_date' in cd and
                cd['start_date'] > cd['end_date']):
            self.add_error('start_date', "Start date must be before or equal to the end date.")

        if (cd.get('template_event') and cd.get('organization') and
                cd['template_event'].organization_id != cd['organization'].id):
            self.add_error('template_event', "Template event and new event must be from the same organization.")

        if 'slug' in cd and cd.get('organization'):
            if Event.objects.filter(organization=cd['organization'], slug=cd['slug']).exists():
                self.add_error('slug', 'Slug is already in use by another event; please choose a different one.')

        return cd

    def _adjust_date(self, old_event, new_event, date):
        """
        Returns a date relative to the new event's start date as the given date
        is relative to the olde event's start date.

        """
        return date + (new_event.start_date - old_event.start_date)

    def save(self):
        if self.instance.is_demo():
            self.instance.api_type = Event.TEST

        self.instance.application_fee_percent = self.instance.organization.default_application_fee_percent

        template = self.cleaned_data.get('template_event')
        if template:
            fields = (
                'description', 'website_url', 'banner_image', 'city',
                'state_or_province', 'country', 'timezone', 'currency',
                'has_dances', 'has_classes', 'liability_waiver', 'privacy',
                'collect_housing_data', 'collect_survey_data', 'cart_timeout',
                'check_postmark_cutoff', 'transfers_allowed', 'facebook_url',
            )
            for field in fields:
                setattr(self.instance, field, getattr(template, field))

        instance = super(EventCreateForm, self).save()

        if template:
            items = Item.objects.filter(event=template).prefetch_related('options', 'images')
            for item in items:
                options = list(item.options.all())
                images = list(item.images.all())
                item.pk = None
                item.event = instance
                item.save()
                for option in options:
                    option.pk = None
                    option.item = item
                    option.available_start = self._adjust_date(template, instance, option.available_start)
                    option.available_end = self._adjust_date(template, instance, option.available_end)
                ItemOption.objects.bulk_create(options)
                for image in images:
                    image.pk = None
                    image.item = item
                ItemImage.objects.bulk_create(images)

            discounts = list(Discount.objects.filter(event=template))
            for discount in discounts:
                discount.pk = None
                discount.event = instance
                discount.available_start = self._adjust_date(template, instance, discount.available_start)
                discount.available_end = self._adjust_date(template, instance, discount.available_end)
            Discount.objects.bulk_create(discounts)

            saved_reports = list(SavedReport.objects.filter(event=template))
            for saved_report in saved_reports:
                saved_report.pk = None
                saved_report.event = instance
            SavedReport.objects.bulk_create(saved_reports)

            forms = CustomForm.objects.filter(event=template).prefetch_related('fields')
            for form in forms:
                fields = list(form.fields.all())
                form.pk = None
                form.event = instance
                form.save()
                for field in fields:
                    field.pk = None
                    field.form = form
                CustomFormField.objects.bulk_create(fields)
        return instance


class EventForm(forms.ModelForm):
    editors = forms.CharField(help_text='Comma-separated email addresses. Each person will be sent an invitation to join the event as an editor.',
                              widget=forms.Textarea,
                              required=False)
    invite_attendees = forms.CharField(help_text='Comma-separated email addresses. Each person will be sent an invitation to the event.',
                                       widget=forms.Textarea,
                                       required=False)

    class Meta:
        model = Event
        fields = ('name', 'slug', 'description', 'website_url', 'banner_image',
                  'city', 'state_or_province', 'country', 'timezone',
                  'currency', 'start_time', 'end_time', 'dance_styles',
                  'has_dances', 'has_classes', 'liability_waiver', 'privacy',
                  'collect_housing_data', 'collect_survey_data',
                  'cart_timeout', 'start_date', 'end_date',
                  'check_postmark_cutoff', 'transfers_allowed', 'facebook_url')
        widgets = {
            'country': forms.Select,
        }

    def __init__(self, request, organization, organization_editable_by, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.request = request
        self.organization = organization
        self.instance.organization = organization
        self.organization_editable_by = organization_editable_by
        if not self.organization_editable_by:
            del self.fields['editors']

        # Always display the timezone that is currently chosen,
        # even if it wouldn't otherwise be displayed.
        timezone = self.instance.timezone
        if (timezone, timezone) not in self.fields['timezone'].choices:
            self.fields['timezone'].choices += ((timezone, timezone),)

        if self.instance.is_demo():
            del self.fields['slug']

        if self.instance.organization.check_payment_allowed:
            self.fields['check_postmark_cutoff'].required = True
        else:
            del self.fields['check_postmark_cutoff']

    def clean_editors(self):
        editors = self.cleaned_data['editors']
        if not editors:
            return []

        validator = EmailValidator()
        # Split email list by commas and trim whitespace:
        editors = [x.strip() for x in editors.split(',')]
        for editor in editors:
            validator(editor)
        return editors

    def clean_invite_attendees(self):
        invite_attendees = self.cleaned_data['invite_attendees']
        if not invite_attendees:
            return []

        validator = EmailValidator()
        # Split email list by commas and trim whitespace:
        invite_attendees = [x.strip() for x in invite_attendees.split(',')]
        for editor in invite_attendees:
            validator(editor)
        return invite_attendees

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        events = Event.objects.filter(
            organization=self.organization,
            slug=slug
        ).exclude(id=self.instance.pk)

        if events.exists():
            raise ValidationError('Slug already in use by another event, '
                                  'please choose a different one.')
        return slug

    def clean(self):
        cleaned_data = super(EventForm, self).clean()
        if ('start_date' in cleaned_data and 'end_date' in cleaned_data and
                cleaned_data['start_date'] > cleaned_data['end_date']):
            raise ValidationError("Start date must be before or equal to "
                                  "the end date.")
        return cleaned_data

    def save(self):
        instance = super(EventForm, self).save()

        if self.organization_editable_by and self.cleaned_data['editors']:
            for editor in self.cleaned_data['editors']:
                invite, created = Invite.objects.get_or_create_invite(
                    email=editor,
                    user=self.request.user,
                    kind=Invite.EVENT_EDITOR,
                    content_id=instance.pk
                )
                if created:
                    invite.send(
                        content=instance,
                        secure=self.request.is_secure(),
                        site=get_current_site(self.request),
                    )

        if self.cleaned_data['invite_attendees']:
            for invite_attendee in self.cleaned_data['invite_attendees']:
                invite, created = Invite.objects.get_or_create_invite(
                    email=invite_attendee,
                    user=self.request.user,
                    kind=Invite.EVENT,
                    content_id=instance.pk
                )
                if created:
                    invite.send(
                        content=instance,
                        secure=self.request.is_secure(),
                        site=get_current_site(self.request),
                    )
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


class ItemOptionForm(forms.ModelForm):
    class Meta:
        model = ItemOption
        exclude = ()

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(ItemOptionForm, self).__init__(*args, **kwargs)
        self.fields['available_end'].initial = event.start_date


class BaseItemOptionFormSet(forms.BaseInlineFormSet):
    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(BaseItemOptionFormSet, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['event'] = self.event
        return super(BaseItemOptionFormSet, self)._construct_form(i, **kwargs)

    @property
    def empty_form(self):
        form = self.form(
            self.event,
            auto_id=self.auto_id,
            prefix=self.add_prefix('__prefix__'),
            empty_permitted=True,
        )
        self.add_fields(form, None)
        return form


ItemOptionFormSet = forms.inlineformset_factory(
    Item,
    ItemOption,
    form=ItemOptionForm,
    formset=BaseItemOptionFormSet,
    extra=0,
    min_num=1,
    validate_min=True,
)


ItemImageFormSet = forms.inlineformset_factory(
    Item,
    ItemImage,
    extra=0,
    exclude=(),
)


class DiscountForm(forms.ModelForm):
    generated_code = None
    item_options = GroupedModelMultipleChoiceField(
                        queryset=ItemOption.objects.all(),
                        group_by_field="item",
                        group_label=lambda x: x.name)

    class Meta:
        model = Discount
        exclude = ('event',)

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(DiscountForm, self).__init__(*args, **kwargs)
        self.fields['item_options'].queryset = ItemOption.objects.filter(item__event=event)
        self.fields['available_end'].initial = event.start_date
        if not self.instance.code:
            self.generated_code = get_random_string(6)
            while Discount.objects.filter(event=self.event,
                                          code=self.generated_code).exists():
                self.generated_code = get_random_string(6)
            self.fields['code'].initial = self.generated_code

    def _post_clean(self):
        super(DiscountForm, self)._post_clean()
        self.instance.event = self.event
        try:
            self.instance.validate_unique()
        except ValidationError as e:
            self._update_errors(e)


class CustomFormForm(forms.ModelForm):
    class Meta:
        model = CustomForm
        exclude = ('event',)

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(CustomFormForm, self).__init__(*args, **kwargs)
        if not event.collect_housing_data:
            choices = CustomForm.FORM_TYPE_CHOICES[:2]
            if self.instance.form_type == CustomForm.HOUSING:
                choices += CustomForm.FORM_TYPE_CHOICES[2:3]
            else:
                choices += CustomForm.FORM_TYPE_CHOICES[3:4]
            self.fields['form_type'].choices = choices

    def _post_clean(self):
        super(CustomFormForm, self)._post_clean()
        self.instance.event = self.event


CustomFormFieldFormSet = forms.inlineformset_factory(
    CustomForm,
    CustomFormField,
    extra=0,
    min_num=1,
    validate_min=True,
    exclude=(),
)


class AttendeeFilterSetForm(forms.Form):
    ORDERING_CHOICES = (
        ("surname", "Surname"),
        ("-surname", "Surname (descending)"),
        ("given_name", "Given Name"),
        ("-given_name", "Given Name (descending)"),
        ("-purchase_date", "Purchase Date (newest first)"),
    )
    HOUSING_STATUS_CHOICES = (("", "---------"),) + Attendee.HOUSING_STATUS_CHOICES

    # TODO: Automatically generate fields from the parent filterset.
    bought_items__item_option = GroupedModelChoiceField(label="Bought Item",
                    queryset=ItemOption.objects.all(),
                    group_by_field="item",
                    group_label=lambda x: x.name,
                    required=False)
    bought_items__discounts__discount = forms.ModelChoiceField(label="Discount",
                                                               queryset=Discount.objects.all(),
                                                               required=False)
    housing_status = forms.ChoiceField(label="Housing Status",
                                       choices=HOUSING_STATUS_CHOICES,
                                       required=False)
    o = forms.ChoiceField(label="Sort by",
                          choices=ORDERING_CHOICES,
                          required=False)

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(AttendeeFilterSetForm, self).__init__(*args, **kwargs)
        option_qs = ItemOption.objects.filter(item__event=self.event).select_related('item')
        self.fields['bought_items__item_option'].queryset = option_qs
        self.fields['bought_items__item_option'].empty_label = 'Any Items'

        discount_qs = Discount.objects.filter(event=self.event)
        self.fields['bought_items__discounts__discount'].queryset = discount_qs
        self.fields['bought_items__discounts__discount'].empty_label = 'Any Discounts'


class ManualPaymentForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ('amount', 'method')

    def __init__(self, order, user, *args, **kwargs):
        super(ManualPaymentForm, self).__init__(*args, **kwargs)
        self.fields['method'].choices = Transaction.METHOD_CHOICES[2:]
        self.order = order
        txn = self.instance
        txn.order = order
        txn.event = order.event
        txn.transaction_type = Transaction.PURCHASE
        txn.created_by = user
        txn.is_confirmed = True
        txn.api_type = txn.event.api_type


class ManualDiscountForm(forms.Form):
    discount = forms.ModelChoiceField(Discount)

    def __init__(self, order, *args, **kwargs):
        super(ManualDiscountForm, self).__init__(*args, **kwargs)
        self.fields['discount'].queryset = Discount.objects.filter(event=order.event)
        self.order = order

    def save(self):
        self.order.add_discount(self.cleaned_data['discount'], force=True)


class OrderNotesForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('notes',)


class AttendeeNotesForm(forms.ModelForm):
    class Meta:
        model = Attendee
        fields = ('notes',)
