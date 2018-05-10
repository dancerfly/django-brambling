from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers, viewsets

from brambling.api.v1.permissions import BaseOrderPermission
from brambling.models import (
    BoughtItem,
    BoughtItemDiscount,
    Discount,
    Order,
    OrderDiscount,
)


class OrderDiscountPermission(BaseOrderPermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            order = view.get_serializer().fields['order'].to_internal_value(request.data.get('order'))
            return self._has_order_permission(request, order)
        return True

    def has_object_permission(self, request, view, orderdiscount):
        # For now, don't allow deletion via the API.
        if request.method == 'DELETE':
            return False

        return self._has_order_permission(request, orderdiscount.order)


class OrderDiscountSerializer(serializers.HyperlinkedModelSerializer):
    discount_name = serializers.CharField(read_only=True)
    discount_code = serializers.CharField()
    link = serializers.HyperlinkedIdentityField(view_name='orderdiscount-detail')
    order = serializers.HyperlinkedRelatedField(view_name='order-detail', queryset=Order.objects.all())

    def __init__(self, *args, **kwargs):
        super(OrderDiscountSerializer, self).__init__(*args, **kwargs)
        # If this is not a creation, set discount_code and order to read_only.
        if self.instance is not None:
            self.fields['discount_code'].read_only = True
            self.fields['order'].read_only = True

    def to_representation(self, instance):
        instance.discount_name = instance.discount.name
        instance.discount_code = instance.discount.code
        return super(OrderDiscountSerializer, self).to_representation(instance)

    def validate(self, data):
        if not data.get('discount_code'):
            raise serializers.ValidationError('Discount code is required.')
        try:
            self.discount = Discount.objects.get(code=data['discount_code'])
        except Discount.DoesNotExist:
            raise serializers.ValidationError("No discount with this code.")
        if data['order'].event != self.discount.event:
            raise serializers.ValidationError("Order and discount are for different events.")
        now = timezone.now()
        if self.discount.available_start > now or self.discount.available_end < now:
            raise serializers.ValidationError("Discount is not currently available.")
        if OrderDiscount.objects.filter(order=data['order'], discount=self.discount):
            raise serializers.ValidationError("Code has already been used.")
        return data

    def create(self, validated_data):
        validated_data.pop('discount_code')
        validated_data['discount'] = self.discount
        instance = super(OrderDiscountSerializer, self).create(validated_data)

        bought_items = BoughtItem.objects.filter(
            order=validated_data['order'],
            item_option__discount=self.discount,
        ).filter(status__in=(
            BoughtItem.UNPAID,
            BoughtItem.RESERVED,
        )).distinct()
        BoughtItemDiscount.objects.bulk_create([
            BoughtItemDiscount(discount=self.discount,
                               bought_item=bought_item,
                               name=self.discount.name,
                               code=self.discount.code,
                               discount_type=self.discount.discount_type,
                               amount=self.discount.amount)
            for bought_item in bought_items
        ])
        return instance

    def update(self, instance, validated_data):
        raise NotImplementedError("Order discounts can't be updated. They just exist.")

    class Meta:
        model = OrderDiscount
        fields = ('discount_name', 'discount_code', 'order', 'timestamp', 'link')


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
                Q(order__event__members=self.request.user) |
                Q(order__event__organization__members=self.request.user)
            )

        # Otherwise, you can view for orders in your session.
        session_orders = Order.objects._get_session(self.request)
        return qs.filter(order__code__in=session_orders.values())
