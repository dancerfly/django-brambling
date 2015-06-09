# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0014_remove_attendee_person_confirmed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='privacy',
            field=models.CharField(default='public', max_length=11, choices=[('public', 'Anyone can find and view the event'), ('link', 'Anyone with a direct link can view the event'), ('half-public', 'Anyone can find and view the event, but only people who are invited can register'), ('invited', 'Only people invited to the event can see the event and register')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='invite',
            name='kind',
            field=models.CharField(max_length=10, choices=[('event', 'Event'), ('editor', 'Event Editor'), ('org_editor', 'Organization Editor')]),
            preserve_default=True,
        ),
    ]
