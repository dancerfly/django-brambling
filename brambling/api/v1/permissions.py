from rest_framework.permissions import BasePermission, SAFE_METHODS

from brambling.models import Order, BoughtItem


class IsAdminUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS or (
                request.user and
                request.user.is_staff
            )
        )


class OrganizationPermission(BasePermission):
    def has_permission(self, request, view):
        # For now, disallow creation via the API.
        if request.method == 'POST':
            return False
        return True

    def has_object_permission(self, request, view, org):
        # Anyone can get a list or detail view.
        if request.method in SAFE_METHODS:
            return True

        # Anyone who can edit the org also has RUD permissions.
        if org.editable_by(request.user):
            return True

        # Disallow deletion (for now, just a blanket).
        if request.method == 'DELETE':
            return False

        return False


class EventPermission(BasePermission):
    def has_permission(self, request, view):
        # For now, disallow creation via the API.
        if request.method == 'POST':
            return False
        return True

    def _has_event_permission(self, request, event):
        # Anyone can view information related to published events.
        if request.method in SAFE_METHODS and event.is_published:
            return True

        # Editors can have CRUD access to published event info.
        if event.editable_by(request.user):
            return True

        return False

    def has_object_permission(self, request, view, event):
        # Disallow deletion of events (for now, just a blanket).
        if request.method == 'DELETE':
            return False

        return self._has_event_permission(request, event)


class ItemPermission(EventPermission):
    def has_object_permission(self, request, view, item):
        return self._has_event_permission(request, item.event)


class ItemImagePermission(EventPermission):
    def has_object_permission(self, request, view, itemimage):
        return self._has_event_permission(request, itemimage.item.event)


class ItemOptionPermission(EventPermission):
    def has_object_permission(self, request, view, itemoption):
        return self._has_event_permission(request, itemoption.item.event)


class OrderPermission(BasePermission):
    def _has_order_permission(self, request, order):
        if order.event.editable_by(request.user):
            return True

        if order.person_id:
            if request.user and request.user.is_authenticated() and order.person_id == request.user.id:
                return True
            return False

        if request.user and request.user.is_authenticated():
            # If this person already has an order for this event,
            # this is not their order. Disallow.
            if Order.objects.filter(person=request.user, event=order.event).exists():
                return False

            # If this person doesn't have an order for this event yet,
            # and this order hasn't been checked out yet, claim it for the user!
            if order.bought_items.filter(status__in=(BoughtItem.BOUGHT, BoughtItem.REFUNDED)).exists():
                order.person = request.user
                order.save()
                return True
        else:
            # Allow if this order is in their session for this event.
            code = Order.objects._get_session_code(request, order.event)
            if code == order.code:
                return True

        return False

    def has_object_permission(self, request, view, obj):
        # Disallow deletion (for now, just a blanket).
        if request.method == 'DELETE':
            return False

        return self._has_order_permission(request, obj)


class OrderSearchPermission(BasePermission):

    def has_permission(self, request, view):
        "Make sure the event is editable by the user trying to view orders."
        event = view.get_event()
        return event.editable_by(request.user)


class AttendeePermission(OrderPermission):
    def has_permission(self, request, view):
        # For now, disallow creation via the API.
        if request.method == 'POST':
            return False
        return True

    def has_object_permission(self, request, view, attendee):
        return self._has_order_permission(request, attendee.order)


class EventHousingPermission(OrderPermission):
    def has_permission(self, request, view):
        # For now, disallow creation via the API.
        if request.method == 'POST':
            return False
        return True

    def has_object_permission(self, request, view, eventhousing):
        if request.method == 'DELETE':
            return False

        return self._has_order_permission(request, eventhousing.order)


class BoughtItemPermission(OrderPermission):
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


class OrderDiscountPermission(OrderPermission):
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
