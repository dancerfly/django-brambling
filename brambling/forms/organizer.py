import datetime

from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
import floppyforms.__future__ as forms

from brambling.models import Event, Item, ItemOption, Discount, Date


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
        cd = self.cleaned_data
        if cd['start_date'] > cd['end_date']:
            raise ValidationError("End date must be before or equal to "
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

ItemOptionFormSet = forms.inlineformset_factory(Item,
                                                ItemOption,
                                                extra=0,
                                                min_num=1,
                                                validate_min=True)


class DiscountForm(forms.ModelForm):
    generated_code = None

    class Meta:
        model = Discount
        exclude = ('event', 'items')

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(DiscountForm, self).__init__(*args, **kwargs)
        self.fields['item_option'].queryset = ItemOption.objects.filter(item__event=event)
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
