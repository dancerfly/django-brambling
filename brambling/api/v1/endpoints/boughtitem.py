from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.fields import empty

from brambling.api.v1.permissions import BaseOrderPermission
from brambling.models import (
    Attendee,
    BoughtItem,
    Order,
)


class BoughtItemPermission(BaseOrderPermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            order = view.get_serializer().fields['order'].to_internal_value(request.data.get('order'))
            return self._has_order_permission(request, order)
        return True

    def has_object_permission(self, request, view, boughtitem):
        # Don't allow deletion if we need this for tracking later.
        if request.method == 'DELETE' and boughtitem.status in (BoughtItem.BOUGHT, BoughtItem.REFUNDED):
            return False

        return self._has_order_permission(request, boughtitem.order)


class BoughtItemSerializer(serializers.HyperlinkedModelSerializer):
    status = serializers.ChoiceField(choices=(BoughtItem.STATUS_CHOICES), default=BoughtItem.RESERVED)
    order = serializers.HyperlinkedRelatedField(view_name='order-detail', queryset=Order.objects.all())
    attendee = serializers.HyperlinkedRelatedField(view_name='attendee-detail', queryset=Attendee.objects.all(), allow_null=True)
    link = serializers.HyperlinkedIdentityField(view_name='boughtitem-detail')
    item_name = serializers.ReadOnlyField()
    item_description = serializers.ReadOnlyField()
    item_option_name = serializers.ReadOnlyField()
    price = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        super(BoughtItemSerializer, self).__init__(*args, **kwargs)

        if self.instance is not None:
            # If this is not a creation, set various fields to read-only
            self.fields['status'].read_only = True
            # Workaround for https://github.com/tomchristie/django-rest-framework/issues/3565
            self.fields['status'].default = empty
            self.fields['order'].read_only = True
            self.fields['item_option'].read_only = True

    def create(self, validated_data):
        item_option = validated_data['item_option']
        validated_data.update({
            'item_name': item_option.item.name,
            'item_description': item_option.item.description,
            'item_option_name': item_option.item.name,
            'price': item_option.price,
        })
        instance = super(BoughtItemSerializer, self).create(validated_data)

        if instance.order.cart_start_time is None:
            instance.order.cart_start_time = timezone.now()
            instance.order.save()

        return instance

    class Meta:
        model = BoughtItem
        fields = (
            'id', 'link', 'item_option', 'order', 'added', 'status', 'attendee',
            'item_name', 'item_description', 'item_option_name', 'price',
        )


class BoughtItemViewSet(viewsets.ModelViewSet):
    queryset = BoughtItem.objects.all()
    serializer_class = BoughtItemSerializer
    permission_classes = [BoughtItemPermission]

    def get_queryset(self):
        qs = self.queryset.all().distinct()

        if 'order' in self.request.GET:
            qs = qs.filter(order=self.request.GET['order'])

        if 'status[]' in self.request.GET:
            qs = qs.filter(status__in=self.request.GET.getlist('status[]'))

        # Superusers can see all the things.
        if self.request.user.is_superuser:
            return qs

        # Otherwise, if you're authenticated, you can see them
        # if the order is yours or you administer the related event.
        if self.request.user.is_authenticated():
            return qs.filter(
                Q(order__person=self.request.user) |
                Q(order__event__members=self.request.user) |
                Q(order__event__organization__members=self.request.user)
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
