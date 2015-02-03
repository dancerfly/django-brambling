# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0014_auto_20150203_2227'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='event',
            field=models.ForeignKey(to='brambling.Event'),
            preserve_default=True,
        ),
    ]
