# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0041_auto_20160104_2321'),
    ]

    operations = [
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
    ]
