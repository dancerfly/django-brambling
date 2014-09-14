# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0034_auto_20140914_0556'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='short_description',
        ),
        migrations.AddField(
            model_name='event',
            name='description',
            field=models.TextField(default='', blank=True),
            preserve_default=False,
        ),
    ]
