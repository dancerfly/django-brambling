# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0023_auto_20140811_0505'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='dwolla_recipient',
            field=models.CharField(default=b'', help_text=b'Dwolla identifier, phone number, or email address', max_length=255, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='stripe_access_token',
            field=models.CharField(default=b'', max_length=32, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='stripe_publishable_key',
            field=models.CharField(default=b'', max_length=32, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='stripe_refresh_token',
            field=models.CharField(default=b'', max_length=32, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='stripe_user_id',
            field=models.CharField(default=b'', max_length=32, blank=True),
            preserve_default=True,
        ),
    ]
