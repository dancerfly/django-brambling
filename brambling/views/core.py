from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.utils import timezone
from django.views.generic import TemplateView, View

from brambling.models import (Event, BoughtItem, Invite, Home, Order, Person,
                              Organization)
from brambling.forms.user import SignUpForm, FloppyAuthenticationForm


class DashboardView(TemplateView):
    template_name = "brambling/dashboard.html"

    def get_context_data(self):
        user = self.request.user
        # TODO: This will probably cause timezone issues in some cases.
        today = timezone.now().date()

        upcoming_events = Event.objects.filter(
            privacy=Event.PUBLIC,
            is_published=True,
        ).filter(start_date__gte=today).order_by('start_date')

        context = {
            'upcoming_events': upcoming_events,
        }

        if user.is_authenticated():
            upcoming_events_interest = Event.objects.filter(
                privacy=Event.PUBLIC,
                dance_styles__person=user,
                is_published=True,
            ).filter(start_date__gte=today).order_by('start_date')

            admin_events = Event.objects.filter(
                Q(organization__owner=user) |
                Q(organization__editors=user) |
                Q(additional_editors=user)
            ).order_by('-last_modified')

            # Registered events is upcoming things you are / might be going to.
            # So you've paid for something or you're going to.
            registered_events_qs = Event.objects.filter(
                order__person=user,
                order__bought_items__status__in=(BoughtItem.BOUGHT, BoughtItem.RESERVED),
            ).filter(start_date__gte=today).order_by('start_date')
            registered_events = list(registered_events_qs)
            re_dict = dict((e.pk, e) for e in registered_events)
            orders = Order.objects.filter(
                person=user,
                bought_items__status=BoughtItem.RESERVED,
                event__in=registered_events
            )
            for order in orders:
                order.event = re_dict[order.event_id]
                order.event.order = order

            # Exclude registered events
            upcoming_events_interest = upcoming_events_interest.exclude(pk__in=registered_events_qs)
            upcoming_events = upcoming_events.exclude(pk__in=registered_events_qs)

            # Past events is things you at one point paid for.
            # So you've paid for something, even if it was later refunded.
            past_events = Event.objects.filter(
                order__person=user,
                order__bought_items__status__in=(BoughtItem.BOUGHT, BoughtItem.REFUNDED),
            ).filter(start_date__lt=today).order_by('-start_date')
            context.update({
                'upcoming_events_interest': upcoming_events_interest,
                'upcoming_events': upcoming_events,
                'admin_events': admin_events,
                'registered_events': registered_events,
                'past_events': past_events,
                'organizations': user.get_organizations(),
            })

        return context


class InviteAcceptView(TemplateView):
    template_name = 'brambling/invite.html'

    def get(self, request, *args, **kwargs):
        try:
            invite = Invite.objects.get(code=kwargs['code'])
        except Invite.DoesNotExist:
            invite = None
        else:
            if request.user.is_authenticated() and request.user.email == invite.email:
                if invite.kind == Invite.EVENT_EDITOR:
                    event = Event.objects.get(pk=invite.content_id)
                    event.additional_editors.add(request.user)
                    url = reverse('brambling_event_update', kwargs={'event_slug': event.slug, 'organization_slug': event.organization.slug})
                elif invite.kind == Invite.HOME:
                    old_home = request.user.home
                    home = Home.objects.get(pk=invite.content_id)
                    request.user.home = home
                    request.user.save()
                    if old_home and not old_home.residents.exists():
                        old_home.delete()
                    url = reverse('brambling_home')
                elif invite.kind == Invite.ORGANIZATION_EDITOR:
                    organization = Organization.objects.get(pk=invite.content_id)
                    organization.editors.add(request.user)
                    url = reverse('brambling_organization_update', kwargs={'organization_slug': organization.slug})
                invite.delete()
                return HttpResponseRedirect(url)
        self.invite = invite
        return super(InviteAcceptView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InviteAcceptView, self).get_context_data(**kwargs)
        if self.invite:
            invited_person_exists = Person.objects.filter(email=self.invite.email).exists()
        else:
            invited_person_exists = False
        context.update({
            'invite': self.invite,
            'invited_person_exists': invited_person_exists,
            'signup_form': SignUpForm(self.request),
            'login_form': FloppyAuthenticationForm(),
        })
        if self.invite:
            context['signup_form'].initial['email'] = self.invite.email
            context['login_form'].initial['username'] = self.invite.email
        return context


class InviteSendView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404
        invite = Invite.objects.get(code=kwargs['code'])
        if invite.kind == Invite.EVENT_EDITOR:
            content = Event.objects.filter(pk=invite.content_id).select_related('organization').get()
            if content.organization.owner_id != self.request.user.pk:
                raise Http404
            url = reverse('brambling_event_update', kwargs={'event_slug': content.slug, 'organization_slug': content.organization.slug})
        elif invite.kind == Invite.HOME:
            if not Home.objects.filter(pk=invite.content_id, residents=request.user).exists():
                raise Http404
            content = Home.objects.get(pk=invite.content_id)
            url = reverse('brambling_home')
        elif invite.kind == Invite.ORGANIZATION_EDITOR:
            content = Organization.objects.get(pk=invite.content_id)
            if content.owner_id != self.request.user.pk:
                raise Http404
            url = reverse('brambling_organization_update', kwargs={'organization_slug': content.slug})
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
        if invite.kind == Invite.EVENT_EDITOR:
            event = Event.objects.filter(pk=invite.content_id).select_related('organization').get()
            if not event.organization.editable_by(self.request.user):
                raise Http404
            url = reverse('brambling_event_update', kwargs={'event_slug': event.slug, 'organization_slug': event.organization.slug})
        elif invite.kind == Invite.HOME:
            if not Home.objects.filter(pk=invite.content_id, residents=request.user).exists():
                raise Http404
            url = reverse('brambling_home')
        elif invite.kind == Invite.ORGANIZATION_EDITOR:
            organization = Organization.objects.get(pk=invite.content_id)
            if organization.owner_id != self.request.user.pk:
                raise Http404
            url = reverse('brambling_organization_update_permissions', kwargs={'organization_slug': organization.slug})
        invite.delete()
        messages.success(request, "Invitation for {} canceled.".format(invite.email))
        return HttpResponseRedirect(url)


class ExceptionView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404
        raise Exception("You did it now!")
