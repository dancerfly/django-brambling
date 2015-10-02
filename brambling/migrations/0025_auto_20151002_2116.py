# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0024_auto_20150924_1842'),
    ]

    operations = [
        migrations.AlterField(
            model_name='boughtitem',
            name='status',
            field=models.CharField(default='unpaid', max_length=11, choices=[('reserved', 'Reserved'), ('unpaid', 'Unpaid'), ('bought', 'Bought'), ('refunded', 'Refunded'), ('transferred', 'Transferred')]),
            preserve_default=True,
        ),
    ]
