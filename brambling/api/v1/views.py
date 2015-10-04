from django.db.models import Q
from django.http import Http404
from rest_framework import viewsets, serializers, status, filters
from rest_framework.response import Response

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
    OrderDiscountPermission,
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
    OrderDiscountSerializer,
)
from brambling.models import (Order, EventHousing, BoughtItem,
                              EnvironmentalFactor, HousingCategory,
                              ItemOption, Item, ItemImage, Attendee, Event,
                              Organization, DanceStyle, OrderDiscount,
                              Discount, Event)


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
            'bought_items', 'discounts',
        ).select_related(
            'event', 'person', 'eventhousing',
        )

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
        session_orders = Order.objects._get_session(self.request)
        return qs.filter(code__in=session_orders.values())

    def create(self, request, *args, **kwargs):
        # Bypass the serializer altogether. This actually performs
        # a get_or_create (essentially) and returns a 201 or 200 response
        # accordingly.
        if not request.data.get('event'):
            raise serializers.ValidationError('Event must be provided')

        try:
            event = Event.objects.get(pk=request.data['event'])
        except Event.DoesNotExist:
            raise serializers.ValidationError('Invalid event id.')

        if len(request.data) > 1:
            raise serializers.ValidationError('Endpoint only accepts event id.')

        order, created = Order.objects.for_request(event, request)

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class OrderSearchViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = (filters.SearchFilter,)
    permission_classes = [OrderPermission]
    search_fields = ("code", "person__given_name", "person__middle_name",
        "person__surname", "attendees__given_name",
        "attendees__middle_name", "attendees__surname")

    def get_queryset(self):
        qs = super(OrderSearchViewSet, self).get_queryset()
        event_id = self.request.query_params.get('event', None)
        if event_id is None:
            raise Http404('No event id specified.')
        return qs.filter(event=event_id)



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
        session_orders = Order.objects._get_session(self.request)
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
        session_orders = Order.objects._get_session(self.request)
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
        session_orders = Order.objects._get_session(self.request)
        return qs.filter(order__code__in=session_orders.values())

    def perform_destroy(self, instance):
        order = instance.order
        instance.delete()
        if not order.has_cart():
            order.cart_start_time = None
            order.save()


class OrderDiscountViewSet(viewsets.ModelViewSet):
    queryset = OrderDiscount.objects.all()
    serializer_class = OrderDiscountSerializer
    permission_classes = [OrderDiscountPermission]

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
        session_orders = Order.objects._get_session(self.request)
        return qs.filter(order__code__in=session_orders.values())
