# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def check_postmark_cutoff(apps, schema_editor):
    Event = apps.get_model('brambling', 'Event')
    for event in Event.objects.select_related('organization'):
        event.check_postmark_cutoff = event.organization.check_postmark_cutoff
        event.save()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0004_event_check_postmark_cutoff'),
    ]

    operations = [
        migrations.RunPython(check_postmark_cutoff),
    ]
