from django.db.models import Q
from rest_framework import viewsets, serializers, status
from rest_framework.response import Response

from brambling.api.v1.permissions import BaseOrderPermission
from brambling.api.v1.endpoints.boughtitem import BoughtItemSerializer
from brambling.api.v1.endpoints.orderdiscount import OrderDiscountSerializer
from brambling.api.v1.endpoints.eventhousing import EventHousingSerializer
from brambling.models import (
    Event,
    Order,
)


class OrderPermission(BaseOrderPermission):
    def has_object_permission(self, request, view, obj):
        # Disallow deletion (for now, just a blanket).
        if request.method == 'DELETE':
            return False

        return self._has_order_permission(request, obj)


class OrderSerializer(serializers.HyperlinkedModelSerializer):
    bought_items = BoughtItemSerializer(many=True)
    discounts = OrderDiscountSerializer(many=True)
    eventhousing = EventHousingSerializer()
    person = serializers.StringRelatedField()
    link = serializers.HyperlinkedIdentityField(view_name='order-detail')
    event = serializers.HyperlinkedRelatedField(view_name='event-detail', read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'link', 'event', 'person', 'email', 'code', 'cart_start_time',
            'bought_items', 'survey_completed', 'heard_through', 'heard_through_other',
            'send_flyers', 'send_flyers_address', 'send_flyers_address_2',
            'send_flyers_city', 'send_flyers_state_or_province',
            'send_flyers_zip', 'send_flyers_country', 'providing_housing',
            'notes', 'eventhousing', 'discounts',
        )

    def to_representation(self, obj):
        data = super(OrderSerializer, self).to_representation(obj)
        # Workaround for https://github.com/SmileyChris/django-countries/issues/106
        if data['send_flyers_country'] == '':
            data['send_flyers_country'] = ''
        return data


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
                Q(event__members=self.request.user) |
                Q(event__organization__members=self.request.user)
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
