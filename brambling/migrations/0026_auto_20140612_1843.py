# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0025_event_collect_survey_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='itemoption',
            name='max_per_owner',
        ),
        migrations.AlterField(
            model_name='itemoption',
            name='price',
            field=models.DecimalField(max_digits=5, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
