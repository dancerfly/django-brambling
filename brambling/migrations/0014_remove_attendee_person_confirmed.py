# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0013_auto_20150605_1920'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendee',
            name='person_confirmed',
        ),
    ]
