# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0032_auto_20150501_0239'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendee',
            name='event_pass',
        ),
        migrations.RemoveField(
            model_name='item',
            name='category',
        ),
    ]
