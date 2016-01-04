# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0041_auto_20160104_2251'),
    ]

    operations = [
        migrations.RenameField(
            model_name='attendee',
            old_name='first_name',
            new_name='given_name',
        ),
        migrations.RenameField(
            model_name='person',
            old_name='first_name',
            new_name='given_name',
        ),
        migrations.RenameField(
            model_name='savedattendee',
            old_name='first_name',
            new_name='given_name',
        ),
    ]
