from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.db.models import Q, Min, Max
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.generic import TemplateView, View

from brambling.models import Event, BoughtItem, Invite, Home
from brambling.forms.user import SignUpForm, FloppyAuthenticationForm


class UserDashboardView(TemplateView):
    template_name = "brambling/dashboard.html"

    def get_context_data(self):
        user = self.request.user
        today = timezone.now().date()

        upcoming_events = Event.objects.filter(
            privacy=Event.PUBLIC,
            is_published=True,
        ).exclude(
            order__person=user,
            order__bought_items__status=BoughtItem.PAID,
        ).annotate(start_date=Min('dates__date'), end_date=Max('dates__date')
                   ).filter(start_date__gte=today).order_by('start_date')

        upcoming_events_interest = Event.objects.filter(
            privacy=Event.PUBLIC,
            dance_styles__person=user,
            is_published=True,
        ).exclude(
            order__person=user,
            order__bought_items__status=BoughtItem.PAID,
        ).annotate(start_date=Min('dates__date'), end_date=Max('dates__date')
                   ).filter(start_date__gte=today).order_by('start_date')

        admin_events = Event.objects.filter(
            (Q(owner=user) | Q(editors=user)),
        ).annotate(start_date=Min('dates__date'), end_date=Max('dates__date')
                   ).order_by('-last_modified')

        registered_events = Event.objects.filter(
            order__person=user,
            order__bought_items__status=BoughtItem.PAID,
        ).annotate(start_date=Min('dates__date'), end_date=Max('dates__date')
                   ).filter(start_date__gte=today).order_by('-start_date')

        past_events = Event.objects.filter(
            order__person=user,
            order__bought_items__status=BoughtItem.PAID,
        ).annotate(start_date=Min('dates__date'), end_date=Max('dates__date')
                   ).filter(start_date__lt=today).order_by('-start_date')

        return {
            'upcoming_events': upcoming_events,
            'upcoming_events_interest': upcoming_events_interest,
            'admin_events': admin_events,
            'registered_events': registered_events,
            'past_events': past_events,
        }

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserDashboardView, self).dispatch(*args, **kwargs)


class SplashView(TemplateView):
    template_name = 'brambling/splash.html'

    def get_context_data(self):
        today = timezone.now().date()
        upcoming_events = Event.objects.filter(privacy=Event.PUBLIC).annotate(
            start_date=Min('dates__date'), end_date=Max('dates__date')
            ).filter(start_date__gte=today).order_by('start_date')
        return {
            'signup_form': SignUpForm(self.request),
            'login_form': FloppyAuthenticationForm(),
            'upcoming_events': upcoming_events,
        }


class InviteAcceptView(TemplateView):
    template_name = 'brambling/invite.html'

    def get(self, request, *args, **kwargs):
        try:
            invite = Invite.objects.get(code=kwargs['code'])
        except Invite.DoesNotExist:
            invite = None
        else:
            if request.user.is_authenticated() and request.user.email == invite.email:
                if invite.kind == Invite.EDITOR:
                    event = Event.objects.get(pk=invite.content_id)
                    event.editors.add(request.user)
                    url = reverse('brambling_event_update', kwargs={'slug': event.slug})
                elif invite.kind == Invite.HOME:
                    old_home = request.user.home
                    home = Home.objects.get(pk=invite.content_id)
                    request.user.home = home
                    request.user.save()
                    if old_home and not old_home.residents.exists():
                        old_home.delete()
                    url = reverse('brambling_home')
                invite.delete()
                return HttpResponseRedirect(url)
        self.invite = invite
        return super(InviteAcceptView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InviteAcceptView, self).get_context_data(**kwargs)
        context.update({
            'invite': self.invite,
            'signup_form': SignUpForm(self.request),
            'login_form': FloppyAuthenticationForm(),
        })
        context['signup_form'].initial['email'] = self.invite.email
        context['login_form'].initial['username'] = self.invite.email
        return context


class InviteSendView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404
        invite = Invite.objects.get(code=kwargs['code'])
        if invite.kind == Invite.EDITOR:
            if not Event.objects.filter(pk=invite.content_id, owner=request.user).exists():
                raise Http404
            content = Event.objects.get(pk=invite.content_id)
            url = reverse('brambling_event_update', kwargs={'slug': content.slug})
        elif invite.kind == Invite.HOME:
            if not Home.objects.filter(pk=invite.content_id, residents=request.user).exists():
                raise Http404
            content = Home.objects.get(pk=invite.content_id)
            url = reverse('brambling_home')
        else:
            raise Http404
        invite.send(
            content=content,
            secure=request.is_secure(),
            site=get_current_site(request),
        )
        messages.success(request, "Invitation sent to {}.".format(invite.email))
        return HttpResponseRedirect(url)


class InviteDeleteView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404
        invite = Invite.objects.get(code=kwargs['code'])
        if invite.kind == Invite.EDITOR:
            if not Event.objects.filter(pk=invite.content_id, owner=request.user).exists():
                raise Http404
            event = Event.objects.only('slug').get(pk=invite.content_id)
            url = reverse('brambling_event_update', kwargs={'slug': event.slug})
        elif invite.kind == Invite.HOME:
            if not Home.objects.filter(pk=invite.content_id, residents=request.user).exists():
                raise Http404
            url = reverse('brambling_home')
        invite.delete()
        messages.success(request, "Invitation for {} canceled.".format(invite.email))
        return HttpResponseRedirect(url)
