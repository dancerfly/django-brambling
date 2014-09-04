# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0026_auto_20140901_0618'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='end_time',
            field=models.TimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='start_time',
            field=models.TimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
