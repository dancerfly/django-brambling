# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def copy_purchaser(apps, schema_editor):
    Transaction = apps.get_model("brambling", "Transaction")
    for transaction in Transaction.objects.filter(event__isnull=True).select_related('order'):
        transaction.event_id = transaction.order.event_id
        transaction.save()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0013_auto_20150203_2226'),
    ]

    operations = [
        migrations.RunPython(copy_purchaser, lambda *a, **k: None)
    ]
