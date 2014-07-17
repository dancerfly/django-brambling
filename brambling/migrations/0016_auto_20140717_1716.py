# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0015_auto_20140715_2231'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='checked_out',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='order',
            name='cart_owners_set',
        ),
    ]
