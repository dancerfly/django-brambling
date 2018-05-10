from django.db.models import Q
from rest_framework import serializers, viewsets

from brambling.api.v1.permissions import BaseOrderPermission
from brambling.models import (
    Attendee,
    EnvironmentalFactor,
    Order,
)


class AttendeePermission(BaseOrderPermission):
    def has_permission(self, request, view):
        # For now, disallow creation via the API.
        if request.method == 'POST':
            return False
        return True

    def has_object_permission(self, request, view, attendee):
        return self._has_order_permission(request, attendee.order)


class AttendeeSerializer(serializers.HyperlinkedModelSerializer):
    ef_cause = serializers.SlugRelatedField(
        slug_field='name',
        queryset=EnvironmentalFactor.objects.all(),
        many=True,
    )
    ef_avoid = serializers.SlugRelatedField(
        slug_field='name',
        queryset=EnvironmentalFactor.objects.all(),
        many=True,
    )
    order = serializers.HyperlinkedRelatedField(view_name='order-detail', read_only=True)
    link = serializers.HyperlinkedIdentityField(view_name='attendee-detail')
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Attendee
        fields = (
            'id', 'link', 'order', 'first_name', 'middle_name', 'last_name',
            'name_order', 'basic_completed', 'email', 'phone',
            'liability_waiver', 'photo_consent', 'housing_status',
            'housing_completed', 'ef_cause', 'ef_avoid',
            'person_prefer', 'person_avoid', 'housing_prefer',
            'other_needs', 'full_name',
        )

    def get_full_name(self, obj):
        return obj.get_full_name()


class AttendeeViewSet(viewsets.ModelViewSet):
    queryset = Attendee.objects.all()
    serializer_class = AttendeeSerializer
    permission_classes = [AttendeePermission]

    def get_queryset(self):
        qs = self.queryset.all().distinct()

        if 'order' in self.request.GET:
            qs = qs.filter(order=self.request.GET['order'])

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
