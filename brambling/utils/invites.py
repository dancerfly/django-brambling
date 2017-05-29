from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import NOT_PROVIDED
from django.db.models.query import QuerySet
from django.core.urlresolvers import reverse
from django.http import Http404

from brambling.mail import InviteMailer
from brambling.models import (
    BoughtItem,
    Event,
    EventMember,
    Invite,
    Order,
    Organization,
    OrganizationMember,
    Transaction,
)
from brambling.tests.factories import (
    EventFactory,
    OrderFactory,
    OrganizationFactory,
)


registry = {}


def get_invite_class(slug):
    if slug not in registry:
        raise ValueError('Unknown invite type')
    return registry[slug]


def get_invite(request, code, content=NOT_PROVIDED):
    """
    Returns an invite utility class instance wrapping the invite
    with the given code.

    """
    invite = Invite.objects.get(code=code)
    cls = get_invite_class(invite.kind)
    return cls(invite=invite, request=request, content=content)


def get_invite_or_404(*args, **kwargs):
    try:
        return get_invite(*args, **kwargs)
    except Invite.DoesNotExist:
        raise Http404


def register_invite(cls):
    if cls.slug in registry:
        raise ValueError('Invite type with slug {} already registered'.format(cls.slug))
    registry[cls.slug] = cls
    return cls


class BaseInvite(object):
    model = None
    slug = None
    verbose_name = None
    accept_template = None

    def __init__(self, request, invite, content=NOT_PROVIDED):
        self.request = request
        self.invite = invite
        self._content = content

    def get_content(self):
        if self._content is NOT_PROVIDED:
            if self.model is None:
                raise NotImplementedError("Invite model must be provided.")
            self._content = self.model.objects.get(pk=self.invite.content_id)
        return self._content

    def get_sender_display(self):
        if self.invite.user:
            return self.invite.user.get_full_name()
        else:
            raise NotImplementedError

    def accept(self):
        raise NotImplementedError

    def post_accept_url(self):
        raise NotImplementedError

    def manage_allowed(self):
        raise NotImplementedError

    def post_manage_url(self):
        raise NotImplementedError

    def get_mailer(self):
        return InviteMailer(
            site=get_current_site(self.request),
            secure=self.request.is_secure(),
            invite=self.invite,
            content=self.get_content(),
            key="invite_{}".format(self.slug),
        )

    def send(self):
        self.get_mailer().send()
        self.invite.is_sent = True
        self.invite.save()

    @classmethod
    def get_invites(cls, content=None):
        kwargs = {'kind': cls.slug}
        if isinstance(content, QuerySet):
            kwargs['content_id__in'] = [obj.pk for obj in content]
        elif hasattr(content, 'pk'):
            kwargs['content_id'] = content.pk
        else:
            raise ValueError('Content is not an object with a pk or a QuerySet.')
        return Invite.objects.filter(**kwargs)

    @classmethod
    def get_or_create(cls, request, email, content):
        instance, created = Invite.objects.get_or_create_invite(
            email=email,
            user=request.user,
            kind=cls.slug,
            content_id=content.pk,
        )
        invite = cls(request, instance, content)
        return invite, created

    @classmethod
    def _get_fake_content(cls):
        raise NotImplementedError

    @classmethod
    def get_fake_invite(cls, request):
        """Returns a fake invite (i.e. for testing emails)"""
        instance = Invite(
            email='support@dancerfly.com',
            user=request.user,
            kind=cls.slug,
            content_id=0,
        )
        invite = cls(request, instance)
        invite._content = cls._get_fake_content()
        return invite


@register_invite
class EventInvite(BaseInvite):
    model = Event
    slug = 'event'
    verbose_name = 'Can attend event'
    accept_template = 'brambling/invites/event.html'

    def accept(self):
        # Create an order if one doesn't exist already.
        # For invite-only events, this is the only way
        # for people to create an order.
        Order.objects.for_request(
            event=self.get_content(),
            request=self.request,
            create=True
        )

    def post_accept_url(self):
        content = self.get_content()
        return reverse('brambling_event_shop', kwargs={
            'event_slug': content.slug,
            'organization_slug': content.organization.slug
        })

    def manage_allowed(self):
        # Invites can be created or modified by people who
        # can edit the event.
        event = self.get_content()
        return self.request.user.has_perm('edit', event)

    def post_manage_url(self):
        content = self.get_content()
        return reverse('brambling_event_registration', kwargs={
            'event_slug': content.slug,
            'organization_slug': content.organization.slug
        })

    @classmethod
    def _get_fake_content(self):
        return EventFactory.build()


@register_invite
class EventEditInvite(BaseInvite):
    model = Event
    slug = 'event_edit'
    verbose_name = 'Can edit event'
    accept_template = 'brambling/invites/event_edit.html'

    def accept(self):
        member = EventMember.objects.get_or_create(
            person=self.request.user,
            event=self.get_content(),
            defaults={'role': EventMember.EDIT},
        )[0]
        # If they're at VIEW, upgrade them to EDIT.
        if member.role != EventMember.EDIT:
            member.role = EventMember.EDIT
            member.save()

    def post_accept_url(self):
        content = self.get_content()
        return reverse('brambling_event_summary', kwargs={
            'event_slug': content.slug,
            'organization_slug': content.organization.slug
        })

    def manage_allowed(self):
        # Invites can be created or modified by people who
        # can edit the organization.
        event = self.get_content()
        return self.request.user.has_perm('change_permissions', event)

    def post_manage_url(self):
        content = self.get_content()
        return reverse('brambling_event_permissions', kwargs={
            'event_slug': content.slug,
            'organization_slug': content.organization.slug
        })

    @classmethod
    def _get_fake_content(self):
        return EventFactory.build()


@register_invite
class EventViewInvite(BaseInvite):
    model = Event
    slug = 'event_view'
    verbose_name = 'Can view event'
    accept_template = 'brambling/invites/event_view.html'

    def accept(self):
        # If they already have a better permission, this invite
        # doesn't downgrade them.
        EventMember.objects.get_or_create(
            person=self.request.user,
            event=self.get_content(),
            defaults={'role': EventMember.VIEW},
        )

    def post_accept_url(self):
        content = self.get_content()
        return reverse('brambling_event_summary', kwargs={
            'event_slug': content.slug,
            'organization_slug': content.organization.slug
        })

    def manage_allowed(self):
        event = self.get_content()
        return self.request.user.has_perm('change_permissions', event)

    def post_manage_url(self):
        content = self.get_content()
        return reverse('brambling_event_permissions', kwargs={
            'event_slug': content.slug,
            'organization_slug': content.organization.slug
        })

    @classmethod
    def _get_fake_content(self):
        return EventFactory.build()


@register_invite
class OrganizationOwnerInvite(BaseInvite):
    model = Organization
    slug = 'org_owner'
    verbose_name = 'Is organization owner'
    accept_template = 'brambling/invites/org_owner.html'

    def accept(self):
        member = OrganizationMember.objects.get_or_create(
            person=self.request.user,
            organization=self.get_content(),
            defaults={'role': OrganizationMember.OWNER},
        )[0]
        # If they're not at OWNER, upgrade them.
        if member.role != OrganizationMember.OWNER:
            member.role = OrganizationMember.OWNER
            member.save()

    def post_accept_url(self):
        content = self.get_content()
        return reverse('brambling_organization_update', kwargs={
            'organization_slug': content.slug
        })

    def manage_allowed(self):
        # Invites can be created or modified by people who
        # have admin access on the org.
        organization = self.get_content()
        return self.request.user.has_perm('change_permissions', organization)

    def post_manage_url(self):
        content = self.get_content()
        return reverse('brambling_organization_update_permissions', kwargs={
            'organization_slug': content.slug
        })

    @classmethod
    def _get_fake_content(self):
        return OrganizationFactory.build()


@register_invite
class OrganizationEditInvite(BaseInvite):
    model = Organization
    slug = 'org_edit'
    verbose_name = 'Can edit organization'
    accept_template = 'brambling/invites/org_edit.html'

    def accept(self):
        member = OrganizationMember.objects.get_or_create(
            person=self.request.user,
            organization=self.get_content(),
            defaults={'role': OrganizationMember.EDIT},
        )[0]
        # If they're at VIEW, upgrade them to EDIT.
        if member.role == OrganizationMember.VIEW:
            member.role = OrganizationMember.EDIT
            member.save()

    def post_accept_url(self):
        content = self.get_content()
        return reverse('brambling_organization_update', kwargs={
            'organization_slug': content.slug
        })

    def manage_allowed(self):
        # Invites can be created or modified by people who
        # have admin access on the org.
        organization = self.get_content()
        return self.request.user.has_perm('change_permissions', organization)

    def post_manage_url(self):
        content = self.get_content()
        return reverse('brambling_organization_update_permissions', kwargs={
            'organization_slug': content.slug
        })

    @classmethod
    def _get_fake_content(self):
        return OrganizationFactory.build()


@register_invite
class OrganizationViewInvite(BaseInvite):
    model = Organization
    slug = 'org_view'
    verbose_name = 'Can view organization'
    accept_template = 'brambling/invites/org_view.html'

    def accept(self):
        OrganizationMember.objects.get_or_create(
            person=self.request.user,
            organization=self.get_content(),
            defaults={'role': OrganizationMember.VIEW},
        )

    def post_accept_url(self):
        content = self.get_content()
        return reverse('brambling_organization_update', kwargs={
            'organization_slug': content.slug
        })

    def manage_allowed(self):
        # Invites can be created or modified by people who
        # have admin access on the org.
        organization = self.get_content()
        return self.request.user.has_perm('change_permissions', organization)

    def post_manage_url(self):
        content = self.get_content()
        return reverse('brambling_organization_update_permissions', kwargs={
            'organization_slug': content.slug
        })

    @classmethod
    def _get_fake_content(self):
        return OrganizationFactory.build()


@register_invite
class TransferInvite(BaseInvite):
    model = BoughtItem
    slug = 'transfer'
    verbose_name = 'Transfer'
    accept_template = 'brambling/invites/transfer.html'

    def get_sender_display(self):
        if self.invite.user:
            return self.invite.user.get_full_name()
        else:
            return self.get_content().order.email

    def accept(self):
        content = self.get_content()
        if content.status != BoughtItem.BOUGHT:
            self.invite.delete()
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

    def post_accept_url(self):
        event = self.order.event
        return reverse('brambling_event_order_summary', kwargs={
            'organization_slug': event.organization.slug,
            'event_slug': event.slug,
        })

    def manage_allowed(self):
        content = self.get_content()
        try:
            order = Order.objects.for_request(
                request=self.request,
                event=content.order.event,
                create=False,
            )[0]
        except Order.DoesNotExist:
            return False

        if order != content:
            return False

    def post_manage_url(self):
        content = self.get_content()
        event = content.order.event
        return reverse('brambling_event_order_summary', kwargs={
            'organization_slug': event.organization.slug,
            'event_slug': event.slug,
        })

    @classmethod
    def _get_fake_content(self):
        order = OrderFactory.build()
        return BoughtItem(
            order=order,
            item_name='test item',
            item_option_name='test item option',
        )
