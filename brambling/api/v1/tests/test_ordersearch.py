from rest_framework import status
from rest_framework.test import APITestCase

from brambling.tests.factories import (
    EventFactory,
    OrderFactory,
    PersonFactory,
)


class OrderSearchTestCase(APITestCase):
    def setUp(self):
        self.person = PersonFactory(password='password', is_superuser=True)
        self.client.login(username=self.person.email, password='password')
        self.event = EventFactory()
        self.order = OrderFactory(event=self.event)

    def test_get__no_permissions(self):
        self.person.is_superuser = False
        self.person.save()

        response = self.client.get(
            '/api/v1/ordersearch/', {
                'event': self.event.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get__no_event(self):
        response = self.client.get(
            '/api/v1/ordersearch/',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_get__with_event(self):
        event2 = EventFactory()
        OrderFactory(event=event2)
        response = self.client.get(
            '/api/v1/ordersearch/', {
                'event': self.event.pk,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.order.pk)
