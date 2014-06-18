# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0027_person_is_active'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendee',
            name='person_avoid',
        ),
        migrations.RemoveField(
            model_name='attendee',
            name='person_prefer',
        ),
        migrations.RemoveField(
            model_name='eventhousing',
            name='person_avoid',
        ),
        migrations.RemoveField(
            model_name='eventhousing',
            name='person_prefer',
        ),
        migrations.RemoveField(
            model_name='home',
            name='person_avoid',
        ),
        migrations.RemoveField(
            model_name='home',
            name='person_prefer',
        ),
        migrations.RemoveField(
            model_name='person',
            name='person_avoid',
        ),
        migrations.RemoveField(
            model_name='person',
            name='person_prefer',
        ),
    ]
