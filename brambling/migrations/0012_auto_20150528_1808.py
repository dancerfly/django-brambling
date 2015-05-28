# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def cache_boughtitem_values(apps, schema_editor):
    BoughtItem = apps.get_model('brambling', 'BoughtItem')

    for bought_item in BoughtItem.objects.select_related('item_option__item'):
        item_option = bought_item.item_option
        item = item_option.item

        bought_item.item_name = item.name
        bought_item.item_description = item.description
        bought_item.item_option_name = item_option.name
        bought_item.price = item_option.price
        bought_item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0011_auto_20150528_1806'),
    ]

    operations = [
        migrations.RunPython(cache_boughtitem_values, lambda *a, **k: None),
    ]
