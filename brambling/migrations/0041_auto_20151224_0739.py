# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0040_auto_20151223_0821'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='notify_new_purchases',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='notify_product_updates',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
