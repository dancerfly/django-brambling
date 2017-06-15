# encoding: utf-8
import mock

from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import TestCase, RequestFactory

from brambling.models import (
    Attendee,
    BoughtItem,
    OrganizationMember,
    Transaction,
    Person,
)
from brambling.tests.factories import (
    EventFactory,
    OrderFactory,
    AttendeeFactory,
    ItemFactory,
    ItemOptionFactory,
    OrganizationFactory,
    PersonFactory,
    TransactionFactory,
)
from brambling.views.organizer import (
    EventSummaryView,
    AttendeeFilterView,
    OrganizationRemoveMemberView,
    SendReceiptView,
)


class SendReceiptTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        owner = PersonFactory()
        self.event = EventFactory(collect_housing_data=False)
        OrganizationMember.objects.create(
            person=owner,
            organization=self.event.organization,
            role=OrganizationMember.OWNER,
        )
        order = OrderFactory(event=self.event, code='aaaaaaaa')
        self.transaction = TransactionFactory(event=self.event, order=order)
        item = ItemFactory(event=self.event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)
        order.mark_cart_paid(self.transaction)

        AttendeeFactory(order=order, bought_items=order.bought_items.all())

        self.view = SendReceiptView()
        self.view.request = self.factory.get('/')
        self.view.request.user = owner

    def test_txn_not_found(self):
        event = self.event
        self.view.kwargs = {'payment_pk': 0}

        with self.assertRaises(Http404):
            self.view.get(self.view.request, event_slug=event.slug,
                          organization_slug=event.organization.slug)

    def test_txn_not_purchase(self):
        event = self.event
        self.view.kwargs = {'payment_pk': self.transaction.pk}
        self.transaction.transaction_type = Transaction.OTHER
        self.transaction.save()

        with self.assertRaises(Http404):
            self.view.get(self.view.request, event_slug=event.slug,
                          organization_slug=event.organization.slug)

    def test_successful_send(self):
        event = self.event
        self.view.kwargs = {'payment_pk': self.transaction.pk}
        SessionMiddleware().process_request(self.view.request)
        MessageMiddleware().process_request(self.view.request)

        response = self.view.get(self.view.request, event_slug=event.slug,
                                 organization_slug=event.organization.slug)
        self.assertEqual(response.status_code, 302)


class EventSummaryTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_attendee_count__no_housing(self):
        """Attendee count should be present & accurate; housing data shouldn't."""
        event = EventFactory(collect_housing_data=False)
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)
        order.mark_cart_paid(transaction)

        AttendeeFactory(order=order, bought_items=order.bought_items.all())

        view = EventSummaryView()
        view.request = self.factory.get('/')
        view.request.user = AnonymousUser()
        view.event = event
        context_data = view.get_context_data()

        self.assertEqual(context_data['attendee_count'], 1)
        self.assertNotIn('attendee_requesting_count', context_data)
        self.assertNotIn('attendee_arranged_count', context_data)
        self.assertNotIn('attendee_home_count', context_data)

    def test_attendee_count__requesting_housing(self):
        """Attendee count should be present & accurate; housing data should."""
        event = EventFactory(collect_housing_data=True)
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)
        order.mark_cart_paid(transaction)

        AttendeeFactory(
            order=order,
            bought_items=order.bought_items.all(),
            housing_status=Attendee.NEED,
        )

        view = EventSummaryView()
        view.request = self.factory.get('/')
        view.request.user = AnonymousUser()
        view.event = event
        context_data = view.get_context_data()

        self.assertEqual(context_data['attendee_count'], 1)
        self.assertEqual(context_data['attendee_requesting_count'], 1)
        self.assertEqual(context_data['attendee_arranged_count'], 0)
        self.assertEqual(context_data['attendee_home_count'], 0)

    def test_attendee_count__have_housing(self):
        """Attendee count should be present & accurate; housing data should."""
        event = EventFactory(collect_housing_data=True)
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)
        order.mark_cart_paid(transaction)

        AttendeeFactory(
            order=order,
            bought_items=order.bought_items.all(),
            housing_status=Attendee.HAVE,
        )

        view = EventSummaryView()
        view.request = self.factory.get('/')
        view.request.user = AnonymousUser()
        view.event = event
        context_data = view.get_context_data()

        self.assertEqual(context_data['attendee_count'], 1)
        self.assertEqual(context_data['attendee_requesting_count'], 0)
        self.assertEqual(context_data['attendee_arranged_count'], 1)
        self.assertEqual(context_data['attendee_home_count'], 0)

    def test_attendee_count__home_housing(self):
        """Attendee count should be present & accurate; housing data should."""
        event = EventFactory(collect_housing_data=True)
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)
        order.mark_cart_paid(transaction)

        AttendeeFactory(
            order=order,
            bought_items=order.bought_items.all(),
            housing_status=Attendee.HOME,
        )

        view = EventSummaryView()
        view.request = self.factory.get('/')
        view.request.user = AnonymousUser()
        view.event = event
        context_data = view.get_context_data()

        self.assertEqual(context_data['attendee_count'], 1)
        self.assertEqual(context_data['attendee_requesting_count'], 0)
        self.assertEqual(context_data['attendee_arranged_count'], 0)
        self.assertEqual(context_data['attendee_home_count'], 1)


class ModelTableViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_unicode_csv(self):
        event = EventFactory(collect_housing_data=True, currency='GBP')
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)
        order.mark_cart_paid(transaction)

        AttendeeFactory(
            order=order,
            bought_items=order.bought_items.all(),
            housing_status=Attendee.HOME,
        )

        view = AttendeeFilterView()
        view.event = event
        view.request = self.factory.get('/?format=csv')
        view.request.user = AnonymousUser()

        table = view.get_table(Attendee.objects.all())
        response = view.render_to_response({'table': table})
        self.assertEqual(response['content-disposition'], 'attachment; filename="export.csv"')
        content = list(response)
        self.assertIn('£200.00', content[1])


class AttendeeFilterViewTest(TestCase):
    def setUp(self):
        self.event = EventFactory()
        self.order = OrderFactory(event=self.event)
        self.transaction = TransactionFactory(
            event=self.event,
            order=self.order,
        )
        self.item = ItemFactory(event=self.event)
        self.item_option = ItemOptionFactory(price=100, item=self.item)

        self.order.add_to_cart(self.item_option)
        self.order.mark_cart_paid(self.transaction)

        self.attendee = AttendeeFactory(
            order=self.order,
            bought_items=self.order.bought_items.all(),
        )

        self.view = AttendeeFilterView()
        self.view.event = self.event

    def test_get_queryset__includes_bought(self):
        self.assertEqual(
            list(self.view.get_queryset()),
            [self.attendee],
        )

    def test_get_queryset__includes_transferred(self):
        self.order.bought_items.update(status=BoughtItem.TRANSFERRED)
        self.assertEqual(
            list(self.view.get_queryset()),
            [self.attendee],
        )


class OrganizationRemoveMemberViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.organization = OrganizationFactory()
        self.owner = PersonFactory()
        self.owner_member = OrganizationMember.objects.create(
            organization=self.organization,
            person=self.owner,
            role=OrganizationMember.OWNER,
        )
        self.editor = PersonFactory()
        self.editor_member = OrganizationMember.objects.create(
            organization=self.organization,
            person=self.editor,
            role=OrganizationMember.EDIT,
        )
        self.request = self.factory.get('/')
        self.request.user = self.owner
        SessionMiddleware().process_request(self.request)
        MessageMiddleware().process_request(self.request)

        self.view = OrganizationRemoveMemberView()

    def test_member_removed__edit(self):
        response = self.view.get(
            self.request,
            pk=self.editor_member.pk,
            organization_slug=self.organization.slug
        )
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(OrganizationMember.DoesNotExist):
            OrganizationMember.objects.get(
                organization=self.organization,
                person=self.editor,
            )

    def test_member_removed__owner(self):
        # Create a second owner
        owner2 = PersonFactory()
        OrganizationMember.objects.create(
            organization=self.organization,
            person=owner2,
            role=OrganizationMember.OWNER,
        )
        response = self.view.get(
            self.request,
            pk=self.owner_member.pk,
            organization_slug=self.organization.slug
        )
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(OrganizationMember.DoesNotExist):
            OrganizationMember.objects.get(
                organization=self.organization,
                person=self.owner,
            )

    def test_member_not_removed__last_owner(self):
        response = self.view.get(
            self.request,
            pk=self.owner_member.pk,
            organization_slug=self.organization.slug
        )
        self.assertEqual(response.status_code, 302)
        member = OrganizationMember.objects.get(
            organization=self.organization,
            person=self.owner,
        )
        self.assertEqual(member.role, OrganizationMember.OWNER)


class RefundViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.owner = Person.objects.create_user(email="owner@owner.me", password="secret")
        self.non_owner = Person.objects.create_user(email="nonowner@nonowner.me", password="secret")
        self.event = EventFactory(collect_housing_data=False)
        OrganizationMember.objects.create(
            person=self.owner,
            organization=self.event.organization,
            role=OrganizationMember.OWNER,
        )
        order = OrderFactory(event=self.event, code='aaaaaaaa')
        self.transaction = TransactionFactory(event=self.event, order=order)
        item = ItemFactory(event=self.event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)
        order.mark_cart_paid(self.transaction)

        AttendeeFactory(order=order, bought_items=order.bought_items.all())

    def test_user_no_permissions_get(self):
        self.client.login(email="nonowner@nonowner.me", password="secret")
        response = self.client.get(reverse("brambling_event_refund", kwargs={
            'organization_slug': self.event.organization.slug,
            'event_slug': self.event.slug,
            'code': self.transaction.order.code,
            'pk': self.transaction.pk
        }))
        self.assertEqual(response.status_code, 404)

    def test_user_no_permissions_post(self):
        self.client.login(email="nonowner@nonowner.me", password="secret")
        response = self.client.post(reverse("brambling_event_refund", kwargs={
            'organization_slug': self.event.organization.slug,
            'event_slug': self.event.slug,
            'code': self.transaction.order.code,
            'pk': self.transaction.pk
        }))
        self.assertEqual(response.status_code, 404)  # not found

    def test_successful_refund_redirect(self):
        self.transaction.amount = '40'
        self.transaction.save()
        self.client.login(email="owner@owner.me", password="secret")
        data = {
            'amount': '20'
        }
        response = self.client.post(reverse("brambling_event_refund", kwargs={
            'organization_slug': self.event.organization.slug,
            'event_slug': self.event.slug,
            'code': self.transaction.order.code,
            'pk': self.transaction.pk
        }), data)
        self.assertEqual(response.status_code, 302)  # temporary redirect
        self.assertRedirects(response, reverse("brambling_event_order_detail",
                                               kwargs={
                                                   'organization_slug': self.event.organization.slug,
                                                   'event_slug': self.event.slug,
                                                   'code': self.transaction.order.code,
                                               }))

    def test_successful_refund_message(self):
        self.transaction.amount = '40'
        self.transaction.save()
        self.client.login(email="owner@owner.me", password="secret")
        data = {
            'amount': '20'
        }
        response = self.client.post(reverse("brambling_event_refund", kwargs={
            'organization_slug': self.event.organization.slug,
            'event_slug': self.event.slug,
            'code': self.transaction.order.code,
            'pk': self.transaction.pk
        }), data, follow=True)
        ctx_messages = list(response.context['messages'])
        self.assertEqual(ctx_messages[0].level, messages.SUCCESS)

    @mock.patch('brambling.models.Transaction.refund')
    def test_unsuccessful_refund_message(self, refund):
        refund.side_effect = ValueError('Terrible value.')
        self.transaction.amount = '40'
        self.transaction.save()
        self.client.login(email="owner@owner.me", password="secret")
        data = {
            'amount': '20'
        }
        response = self.client.post(reverse("brambling_event_refund", kwargs={
            'organization_slug': self.event.organization.slug,
            'event_slug': self.event.slug,
            'code': self.transaction.order.code,
            'pk': self.transaction.pk
        }), data, follow=True)
        ctx_messages = list(response.context['messages'])
        self.assertEqual(ctx_messages[0].level, messages.ERROR)


class OrderDetailViewTest(TestCase):
    def setUp(self):
        self.owner = Person.objects.create_user(email="owner@owner.me", password="secret")
        self.non_owner = Person.objects.create_user(email="nonowner@nonowner.me", password="secret")
        self.event = EventFactory(collect_housing_data=False)
        OrganizationMember.objects.create(
            person=self.owner,
            organization=self.event.organization,
            role=OrganizationMember.OWNER,
        )
        self.order = OrderFactory(event=self.event, code='aaaaaaaa')
        self.transaction = TransactionFactory(event=self.event, order=self.order)
        item = ItemFactory(event=self.event)
        item_option = ItemOptionFactory(price=100, item=item)

        self.order.add_to_cart(item_option)
        self.order.add_to_cart(item_option)
        self.order.mark_cart_paid(self.transaction)

        self.attendee = AttendeeFactory(order=self.order, bought_items=self.order.bought_items.all())
        self.url = reverse('brambling_event_order_detail', kwargs={
            'event_slug': self.event.slug,
            'organization_slug': self.event.organization.slug,
            'code': self.order.code,
        })

    def test_post__order_notes(self):
        self.client.login(username=self.owner.email, password='secret')
        response = self.client.post(
            self.url,
            {
                'is_notes_form': '1',
                'notes': 'Hello',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://testserver{}'.format(self.url))
        self.order.refresh_from_db()
        self.assertEqual(self.order.notes, 'Hello')

    def test_post__attendee_notes(self):
        self.client.login(username=self.owner.email, password='secret')
        response = self.client.post(
            self.url,
            {
                'is_attendee_form': '1',
                'attendee_id': str(self.attendee.pk),
                'notes': 'Hello',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://testserver{}'.format(self.url))
        self.attendee.refresh_from_db()
        self.assertEqual(self.attendee.notes, 'Hello')
