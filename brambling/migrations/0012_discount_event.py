# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0011_discount_item_option'),
    ]

    operations = [
        migrations.AddField(
            model_name='discount',
            name='event',
            field=models.ForeignKey(to='brambling.Event', to_field='id'),
            preserve_default=True,
        ),
    ]
