# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0034_auto_20151104_0259'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='city',
            field=models.CharField(max_length=50, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='country',
            field=django_countries.fields.CountryField(default='US', max_length=2, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='state_or_province',
            field=models.CharField(max_length=50, verbose_name='state / province', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='organization',
            name='default_application_fee_percent',
            field=models.DecimalField(default=1.5, max_digits=5, decimal_places=2, validators=[django.core.validators.MaxValueValidator(100), django.core.validators.MinValueValidator(0)]),
            preserve_default=True,
        ),
    ]
