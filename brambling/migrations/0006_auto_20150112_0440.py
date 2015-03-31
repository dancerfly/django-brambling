# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0005_auto_20150112_0152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(max_length=11, choices=[(b'in_progress', 'In progress'), (b'pending', 'Payment pending'), (b'completed', 'Completed'), (b'refunded', 'Refunded')]),
        ),
    ]
