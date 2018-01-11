from django.db import IntegrityError
from django.test import TestCase

from brambling.models import ProcessedStripeEvent
from brambling.tests.factories import ProcessedStripeEventFactory


class ProcessedStripeEventTestCase(TestCase):
    def test_should_allow_events_with_same_id_if_different_api_type(self):
        event_id = '1'

        ProcessedStripeEventFactory(
            stripe_event_id=event_id,
            api_type=ProcessedStripeEvent.LIVE,
        )

        ProcessedStripeEvent.objects.create(
            stripe_event_id=event_id,
            api_type=ProcessedStripeEvent.TEST,
        )

    def test_api_type_and_event_id_should_be_unique_together(self):
        event_id = '1'

        ProcessedStripeEventFactory(
            stripe_event_id=event_id,
            api_type=ProcessedStripeEvent.LIVE,
        )

        with self.assertRaises(IntegrityError):
            ProcessedStripeEvent.objects.create(
                stripe_event_id=event_id,
                api_type=ProcessedStripeEvent.LIVE,
            )

    def test_barf(self):
        ProcessedStripeEvent.objects.create(
            stripe_event_id='qq',
            api_type='barf',
        )
