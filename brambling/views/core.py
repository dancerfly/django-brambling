from django.contrib.auth.decorators import login_required
from django.db.models import Q, Min
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.generic import TemplateView

from brambling.models import Event


class UserDashboardView(TemplateView):
    template_name = "brambling/dashboard.html"

    def get_context_data(self):
        user = self.request.user
        today = timezone.now().date()

        upcoming_events = Event.objects.filter(
            privacy=Event.PUBLIC,
            dance_styles__person=user,
        ).annotate(start_date=Min('dates__date')
                   ).filter(start_date__gte=today).order_by('start_date')

        admin_events = Event.objects.filter(
            (Q(owner=user) | Q(editors=user)),
        ).order_by('-last_modified')

        registered_events = Event.objects.filter(
            eventperson__person=user,
        ).annotate(start_date=Min('dates__date')
                   ).filter(start_date__gte=today).order_by('-start_date')
        return {
            'upcoming_events': upcoming_events,
            'admin_events': admin_events,
            'registered_events': registered_events,
        }

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserDashboardView, self).dispatch(*args, **kwargs)


class SplashView(TemplateView):
    template_name = 'brambling/splash.html'
