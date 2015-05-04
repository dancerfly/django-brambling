# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0028_auto_20150327_2158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='privacy',
            field=models.CharField(default='public', help_text="Who can view this event once it's published.", max_length=7, choices=[('public', 'List publicly'), ('link', 'Visible to anyone with the link')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='invite',
            name='kind',
            field=models.CharField(max_length=10, choices=[('home', 'Home'), ('editor', 'Event Editor'), ('org_editor', 'Organization Editor')]),
            preserve_default=True,
        ),
    ]
