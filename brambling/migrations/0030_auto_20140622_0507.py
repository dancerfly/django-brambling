# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0029_auto_20140618_0753'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='has_classes',
            field=models.BooleanField(default=False, verbose_name=b'Is a class / Has class(es)'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='has_dances',
            field=models.BooleanField(default=False, verbose_name=b'Is a dance / Has dance(s)'),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='dancestyle',
            name='common_event_types',
        ),
        migrations.RemoveField(
            model_name='event',
            name='event_type',
        ),
        migrations.RemoveField(
            model_name='person',
            name='event_types',
        ),
        migrations.DeleteModel(
            name='EventType',
        ),
    ]
