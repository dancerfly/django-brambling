# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0010_auto_20150528_1805'),
    ]

    operations = [
        migrations.AddField(
            model_name='boughtitem',
            name='item_description',
            field=models.TextField(blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='boughtitem',
            name='item_name',
            field=models.CharField(default='', max_length=30),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='boughtitem',
            name='item_option_name',
            field=models.CharField(default='', max_length=30),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='boughtitem',
            name='price',
            field=models.DecimalField(default=0, max_digits=6, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='boughtitem',
            name='item_option',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.ItemOption', null=True),
            preserve_default=True,
        ),
    ]
