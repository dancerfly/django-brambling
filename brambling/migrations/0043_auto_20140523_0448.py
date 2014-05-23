# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0042_auto_20140523_0238'),
    ]

    operations = [
        migrations.AddField(
            model_name='housingslot',
            name='eventhousing',
            field=models.ForeignKey(to='brambling.EventHousing', default=1, to_field='id'),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='housingslot',
            name=b'home',
        ),
        migrations.RemoveField(
            model_name='housingslot',
            name=b'event',
        ),
    ]
