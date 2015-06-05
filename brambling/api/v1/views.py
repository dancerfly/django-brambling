from django.db.models import Q
from rest_framework import viewsets, serializers, status
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
    BoughtItemCreateSerializer,
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
        session_orders = self.request.session.get(ORDER_CODE_SESSION_KEY, {})
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

        order = None
        created = False

        # First, check if the user is authenticated and has an order for this event.
        if request.user.is_authenticated():
            try:
                order = Order.objects.get(
                    event=event,
                    person=request.user,
                )
            except Order.DoesNotExist:
                pass

        # Next, check if there's a session-stored order. Transfer it
        # if the order hasn't checked out yet and the user is authenticated.
        if order is None:
            session_orders = self.request.session.get(ORDER_CODE_SESSION_KEY, {})
            if str(event.pk) in session_orders:
                code = session_orders[str(event.pk)]
                try:
                    order = Order.objects.get(
                        event=event,
                        person__isnull=True,
                        code=code,
                    )
                except Order.DoesNotExist:
                    pass
                else:
                    if request.user.is_authenticated():
                        if not order.bought_items.filter(status__in=(BoughtItem.BOUGHT, BoughtItem.REFUNDED)).exists():
                            order.person = request.user
                            order.save()
                        else:
                            order = None

        if order is None:
            # Okay, then create for this user.
            created = True
            event.create_order(request.user)

            if not request.user.is_authenticated():
                session_orders = request.session.get(ORDER_CODE_SESSION_KEY, {})
                session_orders[str(event.pk)] = code
                request.session[ORDER_CODE_SESSION_KEY] = session_orders

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


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

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BoughtItemCreateSerializer
        return self.serializer_class

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
        session_orders = self.request.session.get(ORDER_CODE_SESSION_KEY, {})
        return qs.filter(order__code__in=session_orders.values())
