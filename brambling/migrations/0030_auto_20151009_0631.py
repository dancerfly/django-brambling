# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0029_remove_person_modified_directly'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendee',
            name='person',
        ),
        migrations.AddField(
            model_name='attendee',
            name='saved_attendee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.SavedAttendee', null=True),
            preserve_default=True,
        ),
    ]
