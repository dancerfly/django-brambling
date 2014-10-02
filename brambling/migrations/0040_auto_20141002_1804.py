# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0039_remove_event_tagline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemoption',
            name='price',
            field=models.DecimalField(max_digits=6, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
