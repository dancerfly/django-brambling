import django_filters

from brambling.forms.organizer import AttendeeFilterSetForm
from brambling.models import Attendee, ItemOption, Discount, Order


class AttendeeFilterSet(django_filters.FilterSet):
    """
    FilterSet for attendees of an event. Requires the event as its first argument.

    """

    def __init__(self, event, *args, **kwargs):
        "Limit the Item Option list to items belonging to this event."

        super(AttendeeFilterSet, self).__init__(*args, **kwargs)
        self.event = event
        self.filters['bought_items__item_option'].extra.update({
            'queryset': ItemOption.objects.filter(item__event=self.event),
            'empty_label': 'Any Items',
        })
        self.filters['bought_items__discounts__discount'].extra.update({
            'queryset': Discount.objects.filter(event=self.event),
            'empty_label': 'Any Discounts',
        })
        if not event.collect_housing_data:
            del self.filters['housing_status']

    @property
    def form(self):
        if not hasattr(self, '_form'):
            if self.is_bound:
                self._form = AttendeeFilterSetForm(self.data, prefix=self.form_prefix)
            else:
                self._form = AttendeeFilterSetForm(prefix=self.form_prefix)
        return self._form

    class Meta:
        model = Attendee
        fields = ['bought_items__item_option', 'housing_status',
                  'bought_items__discounts__discount']
        order_by = ['name', '-name']


class OrderFilterSet(django_filters.FilterSet):
    class Meta:
        model = Order
        fields = ['providing_housing', 'send_flyers']
