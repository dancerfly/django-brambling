# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0019_auto_20150225_0159'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='dwolla_access_token_expires',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='dwolla_refresh_token',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='dwolla_refresh_token_expires',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='dwolla_test_access_token_expires',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='dwolla_test_refresh_token',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='dwolla_test_refresh_token_expires',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='dwolla_access_token_expires',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='dwolla_refresh_token',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='dwolla_refresh_token_expires',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='dwolla_test_access_token_expires',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='dwolla_test_refresh_token',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='dwolla_test_refresh_token_expires',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='dwolla_access_token_expires',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='dwolla_refresh_token',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='dwolla_refresh_token_expires',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='dwolla_test_access_token_expires',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='dwolla_test_refresh_token',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='dwolla_test_refresh_token_expires',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
