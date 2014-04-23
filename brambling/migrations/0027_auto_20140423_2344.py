# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        (b'brambling', b'0026_eventperson_event_pass'),
    ]

    operations = [
        migrations.AlterField(
            model_name=b'eventperson',
            name=b'wakeup',
            field=models.CharField(blank=True, max_length=5, choices=[(b'late', "I'll be up when I'm up"), (b'early', 'There first thing.')]),
        ),
        migrations.AlterField(
            model_name=b'eventperson',
            name=b'bedtime',
            field=models.CharField(blank=True, max_length=5, choices=[(b'late', 'Staying up late'), (b'early', 'Going to bed early')]),
        ),
    ]
