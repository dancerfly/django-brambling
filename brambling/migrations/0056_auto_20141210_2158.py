# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0055_auto_20141208_2059'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='send_flyers_address_2',
            field=models.CharField(default='', max_length=200, verbose_name=b'address line 2', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='send_flyers_zip',
            field=models.CharField(default='', max_length=12, blank=True),
            preserve_default=False,
        ),
    ]
