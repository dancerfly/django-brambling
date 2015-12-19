# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0035_auto_20151202_1727'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='application_fee_percent',
            field=models.DecimalField(default=Decimal('1.5'), max_digits=5, decimal_places=2, validators=[django.core.validators.MaxValueValidator(100), django.core.validators.MinValueValidator(0)]),
            preserve_default=True,
        ),
    ]
