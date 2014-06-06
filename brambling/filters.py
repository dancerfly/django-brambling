import django_filters

from brambling.models import Attendee, ItemOption


class AttendeeFilterSet(django_filters.FilterSet):
    """
    FilterSet for people who have purchased items from an event. Requires
    the event as its first argument.

    """

    def __init__(self, event, *args, **kwargs):
        "Limit the Item Option list to items belonging to this event."

        super(AttendeeFilterSet, self).__init__(*args, **kwargs)
        self.event = event
        self.filters['bought_items__item_option'].extra.update({
            'queryset': ItemOption.objects.filter(item__event=self.event),
            'empty_label': 'Any Items',
        })

    class Meta:
        model = Attendee
        fields = ['bought_items__item_option']
