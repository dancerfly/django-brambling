# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0050_auto_20141204_0209'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='check_zip',
            field=models.CharField(default='', max_length=12, blank=True),
            preserve_default=False,
        ),
    ]
