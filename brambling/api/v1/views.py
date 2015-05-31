from rest_framework import viewsets

from brambling.api.v1.serializers import (
    HousingCategorySerializer,
    EnvironmentalFactorSerializer,
    DanceStyleSerializer,
    PersonSerializer,
    OrganizationSerializer,
    EventSerializer,
    AttendeeSerializer,
    EventHousingSerializer,
    OrderSerializer,
    BoughtItemSerializer,
    ItemSerializer,
    ItemImageSerializer,
    ItemOptionSerializer,
)
from brambling.models import (Order, Person, EventHousing, BoughtItem,
                              EnvironmentalFactor, HousingCategory,
                              ItemOption, Item, ItemImage, Attendee, Event,
                              Organization, DanceStyle)


class HousingCategoryViewSet(viewsets.ModelViewSet):
    queryset = HousingCategory.objects.all()
    serializer_class = HousingCategorySerializer


class EnvironmentalFactorViewSet(viewsets.ModelViewSet):
    queryset = EnvironmentalFactor.objects.all()
    serializer_class = EnvironmentalFactorSerializer


class DanceStyleViewSet(viewsets.ModelViewSet):
    queryset = DanceStyle.objects.all()
    serializer_class = DanceStyleSerializer


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class AttendeeViewSet(viewsets.ModelViewSet):
    queryset = Attendee.objects.all()
    serializer_class = AttendeeSerializer


class EventHousingViewSet(viewsets.ModelViewSet):
    queryset = EventHousing.objects.all()
    serializer_class = EventHousingSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
        'bought_items',
    ).select_related(
        'event', 'person', 'eventhousing'
    )
    serializer_class = OrderSerializer


class BoughtItemViewSet(viewsets.ModelViewSet):
    queryset = BoughtItem.objects.all()
    serializer_class = BoughtItemSerializer


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class ItemImageViewSet(viewsets.ModelViewSet):
    queryset = ItemImage.objects.all()
    serializer_class = ItemImageSerializer


class ItemOptionViewSet(viewsets.ModelViewSet):
    queryset = ItemOption.objects.all()
    serializer_class = ItemOptionSerializer
