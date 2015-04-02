# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0023_auto_20150306_0327'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customform',
            name='form_type',
            field=models.CharField(help_text='Order forms will only display if "collect survey data" is checked in your event settings', max_length=8, choices=[('attendee', 'Attendee'), ('order', 'Order')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='customform',
            name='index',
            field=models.PositiveSmallIntegerField(default=0, help_text='Defines display order if you have multiple forms.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='customform',
            name='name',
            field=models.CharField(help_text='For organization purposes. This will not be displayed to attendees.', max_length=50),
            preserve_default=True,
        ),
    ]
