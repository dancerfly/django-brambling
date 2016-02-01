from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, View

from brambling.models import (BoughtItem, Invite, Order, Person,
                              Transaction, EventMember, OrganizationMember)
from brambling.forms.user import SignUpForm, FloppyAuthenticationForm


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
            if self.invite.user:
                sender_display = self.invite.user.get_full_name()
            elif self.invite.kind == Invite.TRANSFER:
                sender_display = self.content.order.email
        else:
            invited_person_exists = False
            sender_display = ''
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
        if invite.kind == Invite.EVENT:
            Order.objects.for_request(event=content, request=self.request, create=True)
        elif invite.kind == Invite.EVENT_EDIT:
            member = EventMember.objects.get_or_create(
                person=self.request.user,
                event=content,
                defaults={'role': EventMember.EDIT},
            )[0]
            # If they're at VIEW, upgrade them to EDIT.
            if member.role != EventMember.EDIT:
                member.role = EventMember.EDIT
                member.save()
        elif invite.kind == Invite.EVENT_VIEW:
            EventMember.objects.get_or_create(
                person=self.request.user,
                event=content,
                defaults={'role': EventMember.VIEW},
            )
        elif invite.kind == Invite.ORGANIZATION_EDIT:
            member = OrganizationMember.objects.get_or_create(
                person=self.request.user,
                organization=content,
                defaults={'role': OrganizationMember.EDIT},
            )[0]
            # If they're at VIEW, upgrade them to EDIT.
            if member.role != OrganizationMember.EDIT:
                member.role = OrganizationMember.EDIT
                member.save()
        elif invite.kind == Invite.ORGANIZATION_VIEW:
            OrganizationMember.objects.get_or_create(
                person=self.request.user,
                organization=content,
                defaults={'role': OrganizationMember.VIEW},
            )
        elif invite.kind == Invite.TRANSFER:
            if content.status != BoughtItem.BOUGHT:
                invite.delete()
                messages.error(self.request, "Item can no longer be transferred, sorry.")
                self.order = content.order
                return

            # Complete the transfer!
            # Step one: Create a transaction for the transfer on the
            # initiator's side.
            from_txn = Transaction.objects.create(
                transaction_type=Transaction.TRANSFER,
                amount=0,
                method=Transaction.NONE,
                application_fee=0,
                processing_fee=0,
                is_confirmed=True,
                api_type=content.order.event.api_type,
                order=content.order,
                event=content.order.event,
                related_transaction=content.transactions.get(transaction_type=Transaction.PURCHASE),
            )

            # Add the item being transferred to the txn.
            from_txn.bought_items.add(content)

            # Mark the item as transferred.
            content.status = BoughtItem.TRANSFERRED
            content.save()

            # Step two: get or create an order for the current user.
            self.order = order = Order.objects.for_request(
                request=self.request,
                event=content.order.event,
                create=True
            )[0]

            # Step three: Clone the BoughtItem!
            new_item = BoughtItem.objects.create(
                order=order,
                status=BoughtItem.BOUGHT,
                price=content.price,
                item_option=content.item_option,
                item_name=content.item_name,
                item_description=content.item_description,
                item_option_name=content.item_option_name,
            )

            # Step four: Create a transaction on the recipient's side!
            to_txn = Transaction.objects.create(
                transaction_type=Transaction.TRANSFER,
                amount=0,
                method=Transaction.NONE,
                application_fee=0,
                processing_fee=0,
                is_confirmed=True,
                api_type=order.event.api_type,
                order=order,
                event=order.event,
                related_transaction=from_txn,
            )

            # Step five: Add the BoughtItem to the txn!
            to_txn.bought_items.add(new_item)

            # Step six: Check if the attendee should be deleted!
            # I.e. if they don't have any items assigned to them
            # which haven't been refunded or transferred.
            if content.attendee:
                if not content.attendee.bought_items.exclude(status__in=(BoughtItem.REFUNDED, BoughtItem.TRANSFERRED)).exists():
                    content.attendee.delete()
        else:
            raise Http404("Unhandled transaction type.")

    def get_success_url(self):
        invite = self.invite
        content = self.content
        if invite.kind == Invite.EVENT:
            return reverse('brambling_event_shop', kwargs={
                'event_slug': content.slug,
                'organization_slug': content.organization.slug
            })
        elif invite.kind == Invite.EVENT_EDITOR:
            return reverse('brambling_event_summary', kwargs={
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
        if invite.kind == Invite.EVENT:
            if not content.organization.editable_by(self.request.user):
                return False
        elif invite.kind == Invite.EVENT_EDITOR:
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
                )[0]
            except (SuspiciousOperation, Order.DoesNotExist):
                return False

            if order != content:
                return False
        return True

    def get_success_url(self):
        invite = self.invite
        content = self.content
        if invite.kind == Invite.EVENT:
            return reverse('brambling_event_registration', kwargs={
                'event_slug': content.slug,
                'organization_slug': content.organization.slug
            })
        elif invite.kind == Invite.EVENT_EDITOR:
            return reverse('brambling_event_permissions', kwargs={
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
