# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0020_auto_20150226_0744'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='facebook_url',
            field=models.URLField(verbose_name='facebook event URL', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='website_url',
            field=models.URLField(verbose_name='website URL', blank=True),
            preserve_default=True,
        ),
    ]
