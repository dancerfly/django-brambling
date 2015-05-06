# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations
import stripe


def is_saved_forward(apps, schema_editor):
    CreditCard = apps.get_model('brambling', 'CreditCard')
    for card in CreditCard.objects.all():
        is_saved = False
        if card.person is not None:
            customer = None
            stripe_card = None
            if card.api_type == 'live' and card.person.stripe_customer_id:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                customer = stripe.Customer.retrieve(card.person.stripe_customer_id)
            if card.api_type == 'test' and card.person.stripe_test_customer_id:
                stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
                customer = stripe.Customer.retrieve(card.person.stripe_test_customer_id)
            if customer is not None:
                try:
                    stripe_card = customer.cards.retrieve(card.stripe_card_id)
                except stripe.InvalidRequestError:
                    # card doesn't exist
                    pass
            if stripe_card:
                is_saved = True
        card.is_saved = is_saved
        card.save()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0039_creditcard_is_saved'),
    ]

    operations = [
        migrations.RunPython(is_saved_forward, lambda x, y: None),
    ]
