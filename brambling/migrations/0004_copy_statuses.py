# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def boughtitem_status_forward(apps, schema_editor):
    BoughtItem = apps.get_model("brambling", "BoughtItem")
    BoughtItem.objects.filter(status='paid').update(status='bought')


def boughtitem_status_backward(apps, schema_editor):
    BoughtItem = apps.get_model("brambling", "BoughtItem")
    BoughtItem.objects.filter(status='bought').update(status='paid`')


def order_status_forward(apps, schema_editor):
    Order = apps.get_model("brambling", "Order")
    Order.objects.filter(checked_out=True).update(status='completed')
    Order.objects.filter(checked_out=False).update(status='in_progress')


def order_status_backward(apps, schema_editor):
    Order = apps.get_model("brambling", "Order")
    Order.objects.filter(status='completed').update(checked_out=True)
    Order.objects.filter(status='in_progress').update(checked_out=False)


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0003_auto_20150112_0138'),
    ]

    operations = [
        migrations.RunPython(boughtitem_status_forward,
                             boughtitem_status_backward),
        migrations.RunPython(order_status_forward,
                             order_status_backward)
    ]
