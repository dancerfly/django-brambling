from django.db.models import Q
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
from brambling.views.orders import ORDER_CODE_SESSION_KEY


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

    def get_queryset(self):
        qs = Item.objects.all()

        if 'event' in self.request.GET:
            qs = qs.filter(event=self.request.GET['event'])

        return qs


class ItemImageViewSet(viewsets.ModelViewSet):
    queryset = ItemImage.objects.all()
    serializer_class = ItemImageSerializer
    permission_classes = [ItemImagePermission]


class ItemOptionViewSet(viewsets.ModelViewSet):
    queryset = ItemOption.objects.all()
    serializer_class = ItemOptionSerializer
    permission_classes = [ItemOptionPermission]

    def get_queryset(self):
        qs = super(ItemOptionViewSet, self).get_queryset()
        qs = qs.extra(select={
            'taken': """
SELECT COUNT(*) FROM brambling_boughtitem WHERE
brambling_boughtitem.item_option_id = brambling_itemoption.id AND
brambling_boughtitem.status != 'refunded'
"""
        })
        return qs


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [OrderPermission]

    def get_queryset(self):
        qs = Order.objects.prefetch_related(
            'bought_items',
        ).select_related(
            'event', 'person', 'eventhousing',
        )

        if 'event' in self.request.GET:
            qs = qs.filter(event=self.request.GET['event'])

        if 'user' in self.request.GET:
            if self.request.GET['user']:
                qs = qs.filter(person=self.request.GET['user'])
            else:
                qs = qs.filter(person__isnull=True)

        if 'code' in self.request.GET:
            qs = qs.filter(code=self.request.GET['code'])

        # Superusers can see all the things.
        if self.request.user.is_superuser:
            return qs

        # Otherwise, if you're authenticated, you can see them
        # if they are yours or you administer the related event.
        if self.request.user.is_authenticated():
            return qs.filter(
                Q(person=self.request.user) |
                Q(event__additional_editors=self.request.user) |
                Q(event__organization__editors=self.request.user) |
                Q(event__organization__owner=self.request.user)
            )

        # Otherwise, you can view orders in your session.
        session_orders = self.request.session.get(ORDER_CODE_SESSION_KEY, {})
        return qs.filter(code__in=session_orders.values())


class AttendeeViewSet(viewsets.ModelViewSet):
    queryset = Attendee.objects.all()
    serializer_class = AttendeeSerializer
    permission_classes = [AttendeePermission]

    def get_queryset(self):
        qs = self.queryset.all()

        # Superusers can see all the things.
        if self.request.user.is_superuser:
            return qs

        # Otherwise, if you're authenticated, you can see them
        # if the order is yours or you administer the related event.
        if self.request.user.is_authenticated():
            return qs.filter(
                Q(order__person=self.request.user) |
                Q(order__event__additional_editors=self.request.user) |
                Q(order__event__organization__editors=self.request.user) |
                Q(order__event__organization__owner=self.request.user)
            )

        # Otherwise, you can view for orders in your session.
        session_orders = self.request.session.get(ORDER_CODE_SESSION_KEY, {})
        return qs.filter(order__code__in=session_orders.values())


class EventHousingViewSet(viewsets.ModelViewSet):
    queryset = EventHousing.objects.all()
    serializer_class = EventHousingSerializer
    permission_classes = [EventHousingPermission]

    def get_queryset(self):
        qs = self.queryset.all()

        # Superusers can see all the things.
        if self.request.user.is_superuser:
            return qs

        # Otherwise, if you're authenticated, you can see them
        # if the order is yours or you administer the related event.
        if self.request.user.is_authenticated():
            return qs.filter(
                Q(order__person=self.request.user) |
                Q(order__event__additional_editors=self.request.user) |
                Q(order__event__organization__editors=self.request.user) |
                Q(order__event__organization__owner=self.request.user)
            )

        # Otherwise, you can view for orders in your session.
        session_orders = self.request.session.get(ORDER_CODE_SESSION_KEY, {})
        return qs.filter(order__code__in=session_orders.values())


class BoughtItemViewSet(viewsets.ModelViewSet):
    queryset = BoughtItem.objects.all()
    serializer_class = BoughtItemSerializer
    permission_classes = [BoughtItemPermission]

    def get_queryset(self):
        qs = self.queryset.all()

        # Superusers can see all the things.
        if self.request.user.is_superuser:
            return qs

        # Otherwise, if you're authenticated, you can see them
        # if the order is yours or you administer the related event.
        if self.request.user.is_authenticated():
            return qs.filter(
                Q(order__person=self.request.user) |
                Q(order__event__additional_editors=self.request.user) |
                Q(order__event__organization__editors=self.request.user) |
                Q(order__event__organization__owner=self.request.user)
            )

        # Otherwise, you can view for orders in your session.
        session_orders = self.request.session.get(ORDER_CODE_SESSION_KEY, {})
        return qs.filter(order__code__in=session_orders.values())
