# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def cache_boughtitemdiscount_values(apps, schema_editor):
    BoughtItemDiscount = apps.get_model('brambling', 'BoughtItemDiscount')

    for bought_item_discount in BoughtItemDiscount.objects.select_related('discount'):
        discount = bought_item_discount.discount

        bought_item_discount.name = discount.name
        bought_item_discount.code = discount.code
        bought_item_discount.discount_type = discount.discount_type
        bought_item_discount.amount = discount.amount
        bought_item_discount.save()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0017_auto_20150528_1846'),
    ]

    operations = [
        migrations.RunPython(cache_boughtitemdiscount_values, lambda *a, **k: None),
    ]
