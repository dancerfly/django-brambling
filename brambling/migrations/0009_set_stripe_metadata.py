# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import warnings

from django.db import models, migrations

import stripe


def set_stripe_metadata(apps, schema_editor):
    # Try to set remote metadata for all recorded transactions.
    # But don't get too upset if it all fails ;)
    Transaction = apps.get_model('brambling', 'Transaction')
    transactions = Transaction.objects.select_related(
        'order__event__organization'
    ).filter(
        method='stripe',
    )
    for txn in transactions:
        order = txn.order
        event = order.event
        organization = event.organization
        if txn.api_type == 'test' and organization.stripe_test_access_token:
            stripe.api_key = organization.stripe_test_access_token
        elif txn.api_type == 'live' and organization.stripe_access_token:
            stripe.api_key = organization.stripe_access_token
        try:
            if txn.transaction_type == 'purchase':
                remote = stripe.Charge.retrieve(txn.remote_id)
            elif txn.transaction_type == 'refund':
                ch = stripe.Charge.retrieve(txn.related_transaction.remote_id)
                remote = ch.refunds.retrieve(txn.remote_id)
            else:
                continue
            remote.metadata = {
                'order': order.code,
                'event': event.name,
            }
            remote.save()
        except stripe.InvalidRequestError, e:
            warnings.warn("Updating metadata failed: {}".format(e.message))


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0008_auto_20150520_0253'),
    ]

    operations = [
        migrations.RunPython(set_stripe_metadata, lambda *a, **k: None),
    ]
