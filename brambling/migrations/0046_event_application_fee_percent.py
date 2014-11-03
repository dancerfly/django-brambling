# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0045_auto_20141027_1952'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='application_fee_percent',
            field=models.DecimalField(default=2.5, max_digits=5, decimal_places=2, validators=[django.core.validators.MaxValueValidator(100), django.core.validators.MinValueValidator(0)]),
            preserve_default=True,
        ),
    ]
