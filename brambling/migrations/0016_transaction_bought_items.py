# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def transaction_bought_items(apps, schema_editor):
    Transaction = apps.get_model("brambling", "Transaction")
    transactions = Transaction.objects.select_related('order')
    for transaction in transactions:
        transaction.bought_items = transaction.order.bought_items.all()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0015_auto_20150203_2229'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='bought_items',
            field=models.ManyToManyField(related_name='transactions', null=True, to='brambling.BoughtItem', blank=True),
            preserve_default=True,
        ),
        migrations.RunPython(transaction_bought_items, lambda *a, **k: None),
    ]
