# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0044_auto_20141027_1936'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='dwolla_access_token',
            field=models.CharField(default=b'', max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='dwolla_user_id',
            field=models.CharField(default=b'', max_length=20, blank=True),
            preserve_default=True,
        ),
    ]
