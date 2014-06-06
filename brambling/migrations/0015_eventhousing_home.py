# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0014_event_editors'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventhousing',
            name='home',
            field=models.ForeignKey(to_field='id', blank=True, to='brambling.Home', null=True),
            preserve_default=True,
        ),
    ]
