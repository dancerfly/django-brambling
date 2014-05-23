# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0041_auto_20140523_0042'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventperson',
            name='photo_consent',
            field=models.BooleanField(default=False, verbose_name=b'I consent to have my photo taken at this event.'),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name='photos_ok',
        ),
        migrations.AlterField(
            model_name='eventperson',
            name='status',
            field=models.CharField(default=b'have', max_length=4, verbose_name=b'housing status', choices=[(b'need', b'Need housing'), (b'have', b'Already arranged'), (b'host', b'Hosting others')]),
        ),
    ]
