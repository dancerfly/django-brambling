# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0043_remove_event_logo_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendee',
            name='phone',
            field=models.CharField(max_length=50, blank=True),
        ),
    ]
