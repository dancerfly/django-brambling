# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0012_customformfield_help_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dietaryrestriction',
            name='name',
            field=models.CharField(unique=True, max_length=20),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='environmentalfactor',
            name='name',
            field=models.CharField(unique=True, max_length=30),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='housingcategory',
            name='name',
            field=models.CharField(unique=True, max_length=20),
            preserve_default=True,
        ),
    ]
