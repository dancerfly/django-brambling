# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0040_auto_20151223_0821'),
    ]

    operations = [
        migrations.RenameField(
            model_name='attendee',
            old_name='given_name',
            new_name='first_name',
        ),
        migrations.RenameField(
            model_name='attendee',
            old_name='surname',
            new_name='last_name',
        ),
        migrations.RenameField(
            model_name='person',
            old_name='given_name',
            new_name='first_name',
        ),
        migrations.RenameField(
            model_name='person',
            old_name='surname',
            new_name='last_name',
        ),
        migrations.RenameField(
            model_name='savedattendee',
            old_name='given_name',
            new_name='first_name',
        ),
        migrations.RenameField(
            model_name='savedattendee',
            old_name='surname',
            new_name='last_name',
        ),
        migrations.AlterField(
            model_name='attendee',
            name='name_order',
            field=models.CharField(default='GMS', max_length=3, choices=[('GMS', 'First Middle Surname'), ('SGM', 'Surname First Middle'), ('GS', 'First Surname'), ('SG', 'Surname First')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='person',
            name='name_order',
            field=models.CharField(default='GMS', max_length=3, choices=[('GMS', 'First Middle Surname'), ('SGM', 'Surname First Middle'), ('GS', 'First Surname'), ('SG', 'Surname First')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='savedattendee',
            name='name_order',
            field=models.CharField(default='GMS', max_length=3, choices=[('GMS', 'First Middle Surname'), ('SGM', 'Surname First Middle'), ('GS', 'First Surname'), ('SG', 'Surname First')]),
            preserve_default=True,
        ),
    ]
