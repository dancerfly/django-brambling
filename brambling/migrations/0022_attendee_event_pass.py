# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def delete_attendees(apps, schema_editor):
    Attendee = apps.get_model("brambling", "Attendee")
    db_alias = schema_editor.connection.alias
    Attendee.objects.using(db_alias).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0021_auto_20140807_2143'),
    ]

    operations = [
        migrations.RunPython(delete_attendees),
        migrations.AddField(
            model_name='attendee',
            name='event_pass',
            field=models.OneToOneField(default=1, to='brambling.BoughtItem'),
            preserve_default=False,
        ),
    ]
