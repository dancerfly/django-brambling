# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0032_auto_20150424_1849'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='dates',
        ),
        migrations.RemoveField(
            model_name='event',
            name='housing_dates',
        ),
        migrations.RemoveField(
            model_name='housingslot',
            name='night',
        ),
    ]
