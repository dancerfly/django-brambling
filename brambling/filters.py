import django_filters

from brambling.models import EventPerson


class EventPersonFilterSet(django_filters.FilterSet):
    class Meta:
        model = EventPerson
        fields = []
