# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0010_eventperson_to_order'),
    ]

    operations = [
        migrations.RenameField(
            model_name='attendee',
            old_name='event_person',
            new_name='order',
        ),
        migrations.RenameField(
            model_name='boughtitem',
            old_name='event_person',
            new_name='order',
        ),
        migrations.RenameField(
            model_name='eventhousing',
            old_name='event_person',
            new_name='order',
        ),
        migrations.RenameField(
            model_name='payment',
            old_name='event_person',
            new_name='order',
        ),
    ]
