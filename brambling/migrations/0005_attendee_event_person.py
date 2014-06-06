# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0004_attendee_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendee',
            name='event_person',
            field=models.ForeignKey(to='brambling.EventPerson', to_field='id'),
            preserve_default=True,
        ),
    ]
