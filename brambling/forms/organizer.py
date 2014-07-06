import datetime

from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
import floppyforms.__future__ as forms

from brambling.models import Attendee, Event, Item, ItemOption, Discount, Date

from zenaida.forms import (GroupedModelMultipleChoiceField,
                           GroupedModelChoiceField)


class EventForm(forms.ModelForm):
    start_date = forms.DateField()
    end_date = forms.DateField()

    class Meta:
        model = Event
        exclude = ('dates', 'housing_dates', 'owner')
        widgets = {
            'country': forms.Select
        }

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].initial = getattr(self.instance,
                                                    'start_date',
                                                    datetime.date.today)
        self.fields['end_date'].initial = getattr(self.instance,
                                                  'end_date',
                                                  datetime.date.today)

    def clean(self):
        cleaned_data = super(EventForm, self).clean()
        if cleaned_data['start_date'] > cleaned_data['end_date']:
            raise ValidationError("End date must be before or equal to "
                                  "the start date.")
        return cleaned_data

    def save(self):
        created = self.instance.pk is None
        instance = super(EventForm, self).save()
        if {'start_date', 'end_date'} & set(self.changed_data) or created:
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


ItemOptionFormSet = forms.inlineformset_factory(Item,
                                                ItemOption,
                                                form=ItemOptionForm,
                                                formset=BaseItemOptionFormSet,
                                                extra=0,
                                                min_num=1,
                                                validate_min=True)


class DiscountForm(forms.ModelForm):
    generated_code = None
    item_options = GroupedModelMultipleChoiceField(
                        queryset=ItemOption.objects.all(),
                        group_by_field="item",
                        group_label=lambda x: x.name)

    class Meta:
        model = Discount
        exclude = ('event', 'items')

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


class AttendeeFilterSetForm(forms.Form):
    ORDERING_CHOICES = (
        ("name", "Name"),
        ("-name", "Name (descending)"),
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
