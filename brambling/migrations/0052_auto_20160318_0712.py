# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0051_auto_20160228_0106'),
    ]

    operations = [
        migrations.AlterField(
            model_name='boughtitemdiscount',
            name='amount',
            field=models.DecimalField(max_digits=6, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='discount',
            name='amount',
            field=models.DecimalField(verbose_name='discount value', max_digits=6, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='amount',
            field=models.DecimalField(default=0, max_digits=9, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='application_fee',
            field=models.DecimalField(default=0, max_digits=9, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='processing_fee',
            field=models.DecimalField(default=0, max_digits=9, decimal_places=2),
            preserve_default=True,
        ),
    ]
