# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0023_remove_person_dance_styles'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customform',
            name='form_type',
            field=models.CharField(help_text='Order forms will only display if "collect survey data" is checked in your event settings', max_length=8, choices=[('attendee', 'Attendee'), ('order', 'Order'), ('housing', 'Housing'), ('hosting', 'Hosting')]),
            preserve_default=True,
        ),
    ]
