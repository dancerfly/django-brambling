# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def copy_refunds(apps, schema_editor):
    Refund = apps.get_model("brambling", "Refund")
    Transaction = apps.get_model("brambling", "Transaction")
    for refund in Refund.objects.all():
        Transaction.objects.create(
            amount=-1 * refund.amount,
            timestamp=refund.timestamp,
            created_by=refund.issuer,
            method=refund.method,
            transaction_type='refund',
            is_confirmed=True,
            api_type=refund.api_type,
            related_transaction=refund.payment,
            order=refund.order,
            remote_id=refund.remote_id,
        )
    Refund.objects.all().delete()


def create_refunds(apps, schema_editor):
    Refund = apps.get_model("brambling", "Refund")
    Transaction = apps.get_model("brambling", "Transaction")
    transactions = Transaction.objects.filter(transaction_type='refund')
    for transaction in transactions:
        Refund.objects.create(
            order=transaction.order,
            issuer=transaction.created_by,
            payment=transaction.related_transaction,
            timestamp=transaction.timestamp,
            amount=-1 * transaction.amount,
            method=transaction.method,
            remote_id=transaction.remote_id,
            api_type=transaction.api_type,
        )
    transactions.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0009_auto_20150128_2221'),
    ]

    operations = [
        migrations.RunPython(copy_refunds, create_refunds),
    ]
