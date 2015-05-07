# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0038_remove_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='creditcard',
            name='is_saved',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
