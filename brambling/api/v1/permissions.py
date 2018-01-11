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


class BaseEventPermission(BasePermission):
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
        if request.user.has_perm('edit', event):
            return True

        return False

    def has_object_permission(self, request, view, event):
        raise NotImplementedError


class BaseOrderPermission(BasePermission):
    def _has_order_permission(self, request, order):
        if request.user.has_perm('edit', order.event):
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
        raise NotImplementedError
