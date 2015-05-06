# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0034_auto_20150501_0703'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='card',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.CreditCard', null=True),
            preserve_default=True,
        ),
    ]
