import django_filters

from brambling.models import Person


class PersonFilterSet(django_filters.FilterSet):
    class Meta:
        model = Person
        fields = []
