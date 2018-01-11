from django.db.models import Q
from rest_framework import serializers, viewsets

from brambling.api.v1.permissions import BaseOrderPermission
from brambling.models import (
    EventHousing,
    EnvironmentalFactor,
    HousingCategory,
    Order,
)


class EventHousingPermission(BaseOrderPermission):
    def has_permission(self, request, view):
        # For now, disallow creation via the API.
        if request.method == 'POST':
            return False
        return True

    def has_object_permission(self, request, view, eventhousing):
        if request.method == 'DELETE':
            return False

        return self._has_order_permission(request, eventhousing.order)


class EventHousingSerializer(serializers.HyperlinkedModelSerializer):
    ef_present = serializers.SlugRelatedField(
        slug_field='name',
        queryset=EnvironmentalFactor.objects.all(),
        many=True,
    )
    ef_avoid = serializers.SlugRelatedField(
        slug_field='name',
        queryset=EnvironmentalFactor.objects.all(),
        many=True,
    )
    housing_categories = serializers.SlugRelatedField(
        slug_field='name',
        queryset=HousingCategory.objects.all(),
        many=True,
    )
    order = serializers.HyperlinkedRelatedField(view_name='order-detail', read_only=True)
    link = serializers.HyperlinkedIdentityField(view_name='eventhousing-detail')

    class Meta:
        model = EventHousing
        fields = (
            'id', 'link', 'event', 'order', 'contact_name', 'contact_email',
            'contact_phone', 'address', 'address_2', 'city',
            'state_or_province', 'zip_code', 'country',
            'public_transit_access', 'ef_present', 'ef_avoid', 'person_prefer',
            'person_avoid', 'housing_categories',
        )


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
                Q(order__event__members=self.request.user) |
                Q(order__event__organization__members=self.request.user)
            )

        # Otherwise, you can view for orders in your session.
        session_orders = Order.objects._get_session(self.request)
        return qs.filter(order__code__in=session_orders.values())
