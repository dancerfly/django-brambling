import django_filters

from brambling.models import Person, ItemOption


class PersonFilterSet(django_filters.FilterSet):
    """
    FilterSet for people who have purchased items from an event. Requires
    the event as its first argument.

    """

    def __init__(self, event, *args, **kwargs):
        "Limit the Item Option list to items belonging to this event."

        super(PersonFilterSet, self).__init__(*args, **kwargs)
        self.event = event
        self.filters['items_owned__item_option'].extra.update({
            'queryset': ItemOption.objects.filter(item__event=self.event),
            'empty_label': 'Any Items',
        })

    class Meta:
        model = Person
        fields = ['items_owned__item_option',]
