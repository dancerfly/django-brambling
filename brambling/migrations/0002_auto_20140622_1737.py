# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='modified_directly',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='attendee',
            name='ef_avoid_confirm',
        ),
        migrations.RemoveField(
            model_name='attendee',
            name='ef_cause_confirm',
        ),
        migrations.RemoveField(
            model_name='eventhousing',
            name='ef_avoid_confirm',
        ),
        migrations.RemoveField(
            model_name='eventhousing',
            name='ef_present_confirm',
        ),
        migrations.RemoveField(
            model_name='eventhousing',
            name='housing_categories_confirm',
        ),
    ]
