# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0030_auto_20151009_0631'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='person',
            name='ef_avoid',
        ),
        migrations.RemoveField(
            model_name='person',
            name='ef_cause',
        ),
        migrations.RemoveField(
            model_name='person',
            name='housing_prefer',
        ),
        migrations.RemoveField(
            model_name='person',
            name='other_needs',
        ),
        migrations.RemoveField(
            model_name='person',
            name='person_avoid',
        ),
        migrations.RemoveField(
            model_name='person',
            name='person_prefer',
        ),
        migrations.RemoveField(
            model_name='person',
            name='phone',
        ),
    ]
