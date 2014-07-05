# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0007_auto_20140705_2009'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='method',
            field=models.CharField(default='stripe', max_length=6, choices=[(b'stripe', b'Stripe')]),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name='payment',
            old_name='stripe_charge_id',
            new_name='remote_id',
        ),
    ]
