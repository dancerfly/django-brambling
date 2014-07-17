# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0014_auto_20140715_2226'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendee',
            name='name',
        ),
        migrations.RemoveField(
            model_name='attendee',
            name='nickname',
        ),
        migrations.RemoveField(
            model_name='person',
            name='name',
        ),
        migrations.RemoveField(
            model_name='person',
            name='nickname',
        ),
    ]
