# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0051_event_check_zip'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='stripe_refresh_token',
            field=models.CharField(default=b'', max_length=60, blank=True),
        ),
    ]
