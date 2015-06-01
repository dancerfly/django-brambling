from rest_framework import viewsets

from brambling.api.v1.permissions import (
    IsAdminUserOrReadOnly,
    OrganizationPermission,
    EventPermission,
    ItemPermission,
    ItemImagePermission,
    ItemOptionPermission,
    OrderPermission,
    AttendeePermission,
    EventHousingPermission,
    BoughtItemPermission,
)
from brambling.api.v1.serializers import (
    HousingCategorySerializer,
    EnvironmentalFactorSerializer,
    DanceStyleSerializer,
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
from brambling.models import (Order, EventHousing, BoughtItem,
                              EnvironmentalFactor, HousingCategory,
                              ItemOption, Item, ItemImage, Attendee, Event,
                              Organization, DanceStyle)


class HousingCategoryViewSet(viewsets.ModelViewSet):
    queryset = HousingCategory.objects.all()
    serializer_class = HousingCategorySerializer
    permission_classes = [IsAdminUserOrReadOnly]


class EnvironmentalFactorViewSet(viewsets.ModelViewSet):
    queryset = EnvironmentalFactor.objects.all()
    serializer_class = EnvironmentalFactorSerializer
    permission_classes = [IsAdminUserOrReadOnly]


class DanceStyleViewSet(viewsets.ModelViewSet):
    queryset = DanceStyle.objects.all()
    serializer_class = DanceStyleSerializer
    permission_classes = [IsAdminUserOrReadOnly]


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [OrganizationPermission]


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [EventPermission]


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [ItemPermission]


class ItemImageViewSet(viewsets.ModelViewSet):
    queryset = ItemImage.objects.all()
    serializer_class = ItemImageSerializer
    permission_classes = [ItemImagePermission]


class ItemOptionViewSet(viewsets.ModelViewSet):
    queryset = ItemOption.objects.all()
    serializer_class = ItemOptionSerializer
    permission_classes = [ItemOptionPermission]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related(
        'bought_items',
    ).select_related(
        'event', 'person', 'eventhousing'
    )
    serializer_class = OrderSerializer
    permission_classes = [OrderPermission]


class AttendeeViewSet(viewsets.ModelViewSet):
    queryset = Attendee.objects.all()
    serializer_class = AttendeeSerializer
    permission_classes = [AttendeePermission]


class EventHousingViewSet(viewsets.ModelViewSet):
    queryset = EventHousing.objects.all()
    serializer_class = EventHousingSerializer
    permission_classes = [EventHousingPermission]


class BoughtItemViewSet(viewsets.ModelViewSet):
    queryset = BoughtItem.objects.all()
    serializer_class = BoughtItemSerializer
    permission_classes = [BoughtItemPermission]
