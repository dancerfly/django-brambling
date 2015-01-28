# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0010_refund_to_transaction'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='refund',
            name='issuer',
        ),
        migrations.RemoveField(
            model_name='refund',
            name='order',
        ),
        migrations.RemoveField(
            model_name='refund',
            name='payment',
        ),
        migrations.DeleteModel(
            name='Refund',
        ),
    ]
