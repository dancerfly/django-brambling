# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0001_squash_0053_manual'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='send_flyers_zip',
            field=models.CharField(max_length=12, verbose_name=b'zip code', blank=True),
        ),
    ]
