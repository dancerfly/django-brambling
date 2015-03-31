# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0015_auto_20150203_2229'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='check_state_or_province',
            field=models.CharField(max_length=50, verbose_name=b'state / province', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='check_zip',
            field=models.CharField(max_length=12, verbose_name=b'zip / postal code', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='state_or_province',
            field=models.CharField(max_length=50, verbose_name=b'state / province'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='state_or_province',
            field=models.CharField(max_length=50, verbose_name=b'state / province'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='zip_code',
            field=models.CharField(max_length=12, verbose_name=b'zip / postal code', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='home',
            name='state_or_province',
            field=models.CharField(max_length=50, verbose_name=b'state / province'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='home',
            name='zip_code',
            field=models.CharField(max_length=12, verbose_name=b'zip / postal code', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='order',
            name='send_flyers_state_or_province',
            field=models.CharField(max_length=50, verbose_name=b'state / province', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='order',
            name='send_flyers_zip',
            field=models.CharField(max_length=12, verbose_name=b'zip / postal code', blank=True),
            preserve_default=True,
        ),
    ]
