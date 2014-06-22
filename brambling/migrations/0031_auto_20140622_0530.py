# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0030_auto_20140622_0507'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='dance_styles',
            field=models.ManyToManyField(to=b'brambling.DanceStyle', blank=True),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='event',
            name='dance_style',
        ),
    ]
