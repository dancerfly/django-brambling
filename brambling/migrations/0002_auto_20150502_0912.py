# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


# The data is lost, really, but we can at least make this
# "reversible" for testing
def event_pass_backwards(apps, schema_editor):
    Attendee = apps.get_model('brambling', 'Attendee')
    for attendee in Attendee.objects.all():
        attendee.event_pass = attendee.bought_items.all()[0]
        attendee.save()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0001_squashed_0042_remove_person_default_card'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='category',
            field=models.CharField(default='merch', max_length=7, choices=[(b'merch', 'Merchandise'), (b'comp', 'Competition'), (b'class', 'Class/Lesson a la carte'), (b'pass', 'Pass')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='attendee',
            name='event_pass',
            field=models.OneToOneField(related_name=b'event_pass_for', to='brambling.BoughtItem', blank=True, null=True),
            preserve_default=True,
        ),
        migrations.RunPython(lambda x, y: None, event_pass_backwards),
        migrations.RemoveField(
            model_name='attendee',
            name='event_pass',
        ),
        migrations.RemoveField(
            model_name='item',
            name='category',
        ),
    ]
