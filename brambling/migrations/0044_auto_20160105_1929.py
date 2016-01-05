# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def GS_to_FL(apps, schema_editor):
    migrations.AlterField(
        model_name='attendee',
        name='name_order',
        field=models.CharField(default='FML', max_length=3, choices=[('FML', 'First Middle Last'), ('LFM', 'Last First Middle'), ('FL', 'First Last'), ('LF', 'Last First')]),
        preserve_default=True,
    ),
    migrations.AlterField(
        model_name='person',
        name='name_order',
        field=models.CharField(default='FML', max_length=3, choices=[('FML', 'First Middle Last'), ('LFM', 'Last First Middle'), ('FL', 'First Last'), ('LF', 'Last First')]),
        preserve_default=True,
    ),
    migrations.AlterField(
        model_name='savedattendee',
        name='name_order',
        field=models.CharField(default='FML', max_length=3, choices=[('FML', 'First Middle Last'), ('LFM', 'Last First Middle'), ('FL', 'First Last'), ('LF', 'Last First')]),
        preserve_default=True,
    ),	

def FL_to_GS(apps, schema_editor):
    migrations.AlterField(
        model_name='attendee',
        name='name_order',
        field=models.CharField(default='GMS', max_length=3, choices=[('GMS', 'First Middle Last'), ('SGM', 'Last First Middle'), ('GS', 'First Last'), ('SG', 'Last First')]),
        preserve_default=True,
    ),
    migrations.AlterField(
        model_name='person',
        name='name_order',
        field=models.CharField(default='GMS', max_length=3, choices=[('GMS', 'First Middle Last'), ('SGM', 'Last First Middle'), ('GS', 'First Last'), ('SG', 'Last First')]),
        preserve_default=True,
    ),
    migrations.AlterField(
        model_name='savedattendee',
        name='name_order',
        field=models.CharField(default='GMS', max_length=3, choices=[('GMS', 'First Middle Last'), ('SGM', 'Last First Middle'), ('GS', 'First Last'), ('SG', 'Last First')]),
        preserve_default=True,
    ),	
class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0043_auto_20160104_2321'),
    ]

    operations = [
        migrations.RunPython(GS_to_FL, FL_to_GS),
    ]
