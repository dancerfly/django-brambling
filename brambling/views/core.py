from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView, View

from brambling.models import (Event, BoughtItem, Invite, Order, Person,
                              Organization, Transaction)
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
        ).filter(start_date__gte=today).order_by('start_date').distinct()

        context = {
            'upcoming_events': upcoming_events,
        }

        if user.is_authenticated():
            upcoming_events_interest = Event.objects.filter(
                privacy=Event.PUBLIC,
                dance_styles__person=user,
                is_published=True,
            ).filter(start_date__gte=today).order_by('start_date').distinct()

            admin_events = Event.objects.filter(
                Q(organization__owner=user) |
                Q(organization__editors=user) |
                Q(additional_editors=user)
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
            ).filter(start_date__lt=today).order_by('-start_date').distinct()
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
            self.invite = Invite.objects.get(code=kwargs['code'])
        except Invite.DoesNotExist:
            self.invite = None
            self.content = None
        else:
            self.content = self.invite.get_content()
            if request.user.is_authenticated() and request.user.email == self.invite.email:
                if request.user.confirmed_email != request.user.email:
                    request.user.confirmed_email = request.user.email
                    request.user.save()
                self.handle_invite()
                self.invite.delete()
                return HttpResponseRedirect(self.get_success_url())
        return super(InviteAcceptView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InviteAcceptView, self).get_context_data(**kwargs)
        if self.invite:
            invited_person_exists = Person.objects.filter(email=self.invite.email).exists()
        else:
            invited_person_exists = False
        if self.invite.user:
            sender_display = self.invite.user.get_full_name()
        elif self.invite.kind == Invite.TRANSFER:
            sender_display = self.content.order.email
        context.update({
            'invite': self.invite,
            'content': self.content,
            'invited_person_exists': invited_person_exists,
            'sender_display': sender_display,
            'signup_form': SignUpForm(self.request),
            'login_form': FloppyAuthenticationForm(),
        })
        if self.invite:
            context['signup_form'].initial['email'] = self.invite.email
            context['login_form'].initial['username'] = self.invite.email
        return context

    def handle_invite(self):
        invite = self.invite
        content = self.content
        if invite.kind == Invite.EVENT_EDITOR:
            content.additional_editors.add(self.request.user)
        elif invite.kind == Invite.ORGANIZATION_EDITOR:
            content.editors.add(self.request.user)
        elif invite.kind == Invite.TRANSFER:
            if content.status != BoughtItem.BOUGHT:
                invite.delete()
                messages.error(self.request, "Item can no longer be transferred, sorry.")
                self.order = content
                return

            # Complete the transfer!
            # Step one: get or create an order for the current user.
            self.order = order = Order.objects.for_request(
                request=self.request,
                event=content.order.event,
                create=True
            )[1]

            # Step two: Clone the BoughtItem!
            new_item = BoughtItem.objects.create(
                order=order,
                status=BoughtItem.BOUGHT,
                price=content.price,
                item_option=content.item_option,
                item_name=content.item_name,
                item_description=content.item_description,
                item_option_name=content.item_option_name,
            )

            # Step three: Create a transaction!
            txn = Transaction.objects.create(
                transaction_type=Transaction.TRANSFER,
                amount=content.price,
                method=Transaction.FAKE,
                application_fee=0,
                processing_fee=0,
                is_confirmed=True,
                api_type=order.event.api_type,
                order=order,
                event=order.event
            )

            # Step four: Add the BoughtItem to the txn!
            txn.bought_items.add(new_item)

            # Step five: Mark the old version transferred!
            content.status = BoughtItem.TRANSFERRED
            content.save()
        else:
            raise Http404("Unhandled transaction type.")

    def get_success_url(self):
        invite = self.invite
        content = self.content
        if invite.kind == Invite.EVENT_EDITOR:
            return reverse('brambling_event_update', kwargs={
                'event_slug': content.slug,
                'organization_slug': content.organization.slug
            })
        elif invite.kind == Invite.ORGANIZATION_EDITOR:
            return reverse('brambling_organization_update', kwargs={
                'organization_slug': content.slug
            })
        elif invite.kind == Invite.TRANSFER:
            event = self.order.event
            return reverse('brambling_event_order_summary', kwargs={
                'organization_slug': event.organization.slug,
                'event_slug': event.slug,
            })


class InviteManageView(View):
    def get(self, request, *args, **kwargs):
        self.invite = get_object_or_404(Invite, code=kwargs['code'])
        self.content = self.invite.get_content()
        if not self.has_permission():
            raise Http404

        self.do_the_thing()

        return HttpResponseRedirect(self.get_success_url())

    def has_permission(self):
        invite = self.invite
        content = self.content
        if invite.kind == Invite.EVENT_EDITOR:
            if not self.request.user.is_authenticated():
                return False
            if not content.organization.editable_by(self.request.user):
                return False
        elif invite.kind == Invite.ORGANIZATION_EDITOR:
            if not self.request.user.is_authenticated():
                return False
            if content.owner_id != self.request.user.pk:
                return False
        elif invite.kind == Invite.TRANSFER:
            try:
                order = Order.objects.for_request(
                    request=self.request,
                    event=content.order.event,
                    create=False,
                )[1]
            except (SuspiciousOperation, Order.DoesNotExist):
                return False

            if order != content:
                return False
        return True

    def get_success_url(self):
        invite = self.invite
        content = self.content
        if invite.kind == Invite.EVENT_EDITOR:
            return reverse('brambling_event_update', kwargs={
                'event_slug': content.slug,
                'organization_slug': content.organization.slug
            })
        elif invite.kind == Invite.ORGANIZATION_EDITOR:
            return reverse('brambling_organization_update_permissions', kwargs={
                'organization_slug': content.slug
            })
        elif invite.kind == Invite.TRANSFER:
            event = content.order.event
            return reverse('brambling_event_order_summary', kwargs={
                'organization_slug': event.organization.slug,
                'event_slug': event.slug,
            })
        else:
            raise Http404

    def do_the_thing(self):
        raise NotImplementedError("Must be implemented by subclasses")


class InviteSendView(InviteManageView):
    def do_the_thing(self):
        self.invite.send(
            content=self.content,
            secure=self.request.is_secure(),
            site=get_current_site(self.request),
        )
        messages.success(self.request, "Invitation sent to {}.".format(self.invite.email))


class InviteDeleteView(InviteManageView):
    def do_the_thing(self):
        self.invite.delete()
        messages.success(self.request, "Invitation for {} canceled.".format(self.invite.email))


class ExceptionView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404
        raise Exception("You did it now!")
