# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


BOUGHT_ITEM_RESERVED = 'reserved'
BOUGHT_ITEM_UNPAID = 'unpaid'
BOUGHT_ITEM_BOUGHT = 'bought'
BOUGHT_ITEM_REFUNDED = 'refunded'

ORDER_IN_PROGRESS = 'in_progress'
ORDER_PENDING = 'pending'
ORDER_COMPLETED = 'completed'
ORDER_REFUNDED = 'refunded'


def status_backward(apps, schema_editor):
    Order = apps.get_model('brambling', 'Order')
    for order in Order.objects.all():
        if order.bought_items.filter(status=BOUGHT_ITEM_REFUNDED).exists():
            order.status = ORDER_REFUNDED
        elif order.bought_items.filter(status=BOUGHT_ITEM_BOUGHT).exists():
            order.status = ORDER_COMPLETED
        elif order.bought_items.filter(status=BOUGHT_ITEM_RESERVED).exists():
            order.status = ORDER_IN_PROGRESS
        order.save()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0031_auto_20150428_1955'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(default='', max_length=11, choices=[(b'in_progress', 'In progress'), (b'pending', 'Payment pending'), (b'completed', 'Completed'), (b'refunded', 'Refunded')]),
            preserve_default=True,
        ),
        migrations.RunPython(lambda x, y: None, status_backward),
        migrations.RemoveField(
            model_name='order',
            name='status',
        ),
    ]
