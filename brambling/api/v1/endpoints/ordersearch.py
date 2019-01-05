from rest_framework import viewsets, filters
from rest_framework.permissions import BasePermission

from brambling.api.v1.endpoints.order import OrderSerializer
from brambling.models import Order, Event


class OrderSearchPermission(BasePermission):
    def has_permission(self, request, view):
        "Make sure the event is editable by the user trying to view orders."
        event = view.get_event()
        return request.user.has_perm('edit', event)


class OrderSearchViewSet(viewsets.ReadOnlyModelViewSet):
    "A ViewSet that filters orders based on a single search term."
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = (filters.SearchFilter,)
    permission_classes = [OrderSearchPermission]
    search_fields = (
        "code", "person__first_name", "person__middle_name",
        "person__last_name", "attendees__first_name",
        "attendees__middle_name", "attendees__last_name"
    )

    def get_event(self):
        event_id = self.request.query_params.get('event', None)
        return Event.objects.filter(pk=event_id).first()

    def get_queryset(self):
        "Filter orders down to those which are for the specific event provided."

        qs = super(OrderSearchViewSet, self).get_queryset().prefetch_related(
            'bought_items',
        ).select_related(
            'event', 'person', 'eventhousing',
        )

        event = self.get_event()
        if not event:
            return qs.none()

        return qs.filter(event=event)
