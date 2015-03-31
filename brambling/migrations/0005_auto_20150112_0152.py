# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0004_copy_statuses'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='checked_out',
        ),
        migrations.AlterField(
            model_name='boughtitem',
            name='status',
            field=models.CharField(default=b'unpaid', max_length=8, choices=[(b'reserved', 'Reserved'), (b'unpaid', 'Unpaid'), (b'bought', 'Bought'), (b'refunded', 'Refunded')]),
        ),
    ]
