# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0032_event_short_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendee',
            name='phone',
            field=models.CharField(help_text=b'Required if requesting housing', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='contact_phone',
            field=models.CharField(max_length=50),
        ),
    ]
