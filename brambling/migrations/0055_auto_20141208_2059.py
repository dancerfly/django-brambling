# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0054_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventhousing',
            name='zip_code',
            field=models.CharField(default='', max_length=12, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='home',
            name='zip_code',
            field=models.CharField(default='', max_length=12, blank=True),
            preserve_default=False,
        ),
    ]
