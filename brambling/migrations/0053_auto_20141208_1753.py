# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0052_auto_20141205_2042'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventhousing',
            name='address_2',
            field=models.CharField(default='', max_length=200, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='home',
            name='address_2',
            field=models.CharField(default='', max_length=200, blank=True),
            preserve_default=False,
        ),
    ]
