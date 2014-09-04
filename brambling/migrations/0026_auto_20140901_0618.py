# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0025_auto_20140823_0402'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='dwolla_access_token',
            field=models.CharField(default=b'', max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='dwolla_user_id',
            field=models.CharField(default=b'', max_length=20, blank=True),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='event',
            name='dwolla_recipient',
        ),
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(max_length=6, choices=[(b'stripe', b'Stripe'), (b'dwolla', b'Dwolla')]),
        ),
        migrations.AlterField(
            model_name='subrefund',
            name='method',
            field=models.CharField(max_length=6, choices=[(b'stripe', b'Stripe'), (b'dwolla', b'Dwolla')]),
        ),
    ]
