from django.db.models import Q, Prefetch
from django.http import Http404
from django.utils import timezone
from django.views.generic import TemplateView, View

from brambling.models import Event, BoughtItem, Order, Transaction


class DashboardView(TemplateView):
    template_name = "brambling/dashboard.html"

    def get_context_data(self):
        user = self.request.user
        # TODO: This will probably cause timezone issues in some cases.
        today = timezone.now().date()

        upcoming_events = Event.objects.filter(
            privacy__in=(Event.PUBLIC, Event.HALF_PUBLIC),
            is_published=True,
        ).filter(start_date__gte=today).order_by('start_date').distinct()

        context = {
            'upcoming_events': upcoming_events,
        }

        if user.is_authenticated():
            admin_events = Event.objects.filter(
                Q(organization__members=user) |
                Q(members=user)
            ).order_by('-last_modified').distinct()

            # Registered events is upcoming things you are / might be going to.
            # So you've paid for something or you're going to.
            registered_events_qs = Event.objects.filter(
                order__person=user,
                order__bought_items__status__in=(BoughtItem.BOUGHT, BoughtItem.RESERVED),
            ).filter(start_date__gte=today).order_by('start_date').distinct()
            registered_events = list(registered_events_qs)
            re_dict = dict((e.pk, e) for e in registered_events)
            orders = Order.objects.filter(
                person=user,
                bought_items__status__in=(BoughtItem.BOUGHT,
                                          BoughtItem.RESERVED),
                event__in=registered_events
            ).prefetch_related(Prefetch(
                "transactions",
                queryset=Transaction.objects.filter(
                    method=Transaction.CHECK, is_confirmed=False),
                to_attr="unconfirmed_checks")
            )
            for order in orders:
                order.event = re_dict[order.event_id]
                order.event.order = order

            # Exclude registered events
            upcoming_events = upcoming_events.exclude(pk__in=registered_events_qs)

            context.update({
                'upcoming_events': upcoming_events,
                'admin_events': admin_events,
                'registered_events': registered_events,
                'organizations': user.organizations.order_by('-last_modified'),
            })

        return context


class ExceptionView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404
        raise Exception("You did it now!")
