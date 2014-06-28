# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0004_auto_20140625_1729'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discount',
            name='available_end',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='discount',
            name='available_start',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='event',
            name='privacy',
            field=models.CharField(default=b'private', help_text=b'Who can view this event.', max_length=7, choices=[(b'public', 'List publicly'), (b'link', 'Visible to anyone with the link'), (b'private', 'Only visible to owner and editors')]),
        ),
    ]
