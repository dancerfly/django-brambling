# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0016_auto_20150528_1808'),
    ]

    operations = [
        migrations.AddField(
            model_name='boughtitemdiscount',
            name='amount',
            field=models.DecimalField(default=0, max_digits=5, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='boughtitemdiscount',
            name='code',
            field=models.CharField(default='', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='boughtitemdiscount',
            name='discount_type',
            field=models.CharField(default='flat', max_length=7, choices=[('flat', 'Flat'), ('percent', 'Percent')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='boughtitemdiscount',
            name='name',
            field=models.CharField(default='', max_length=40),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='boughtitemdiscount',
            name='discount',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.Discount', null=True),
            preserve_default=True,
        ),
    ]
