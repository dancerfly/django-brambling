# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0052_auto_20141205_2042'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='check_address_2',
            field=models.CharField(default='', max_length=200, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='eventhousing',
            name='address_2',
            field=models.CharField(default='', max_length=200, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='eventhousing',
            name='zip_code',
            field=models.CharField(default='', max_length=12, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='home',
            name='address_2',
            field=models.CharField(default='', max_length=200, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='home',
            name='zip_code',
            field=models.CharField(default='', max_length=12, blank=True),
            preserve_default=False,
        ),
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
