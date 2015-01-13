# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0006_auto_20150112_0440'),
    ]

    operations = [
        migrations.AddField(
            model_name='creditcard',
            name='api_type',
            field=models.CharField(default=b'live', max_length=4, choices=[(b'live', b'Live'), (b'test', b'Test')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='api_type',
            field=models.CharField(default=b'live', max_length=4, choices=[(b'live', 'Live'), (b'test', 'Test')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='dwolla_test_access_token',
            field=models.CharField(default=b'', max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='dwolla_test_user_id',
            field=models.CharField(default=b'', max_length=20, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='stripe_test_access_token',
            field=models.CharField(default=b'', max_length=32, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='stripe_test_publishable_key',
            field=models.CharField(default=b'', max_length=32, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='stripe_test_refresh_token',
            field=models.CharField(default=b'', max_length=60, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='stripe_test_user_id',
            field=models.CharField(default=b'', max_length=32, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='dwolla_test_access_token',
            field=models.CharField(default=b'', max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='dwolla_test_user_id',
            field=models.CharField(default=b'', max_length=20, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='payment',
            name='api_type',
            field=models.CharField(default=b'live', max_length=4, choices=[(b'live', 'Live'), (b'test', 'Test')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='dwolla_test_access_token',
            field=models.CharField(default=b'', max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='dwolla_test_user_id',
            field=models.CharField(default=b'', max_length=20, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='stripe_test_customer_id',
            field=models.CharField(max_length=36, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='refund',
            name='api_type',
            field=models.CharField(default=b'live', max_length=4, choices=[(b'live', 'Live'), (b'test', 'Test')]),
            preserve_default=True,
        ),
    ]
