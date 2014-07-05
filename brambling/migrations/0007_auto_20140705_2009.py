# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0006_auto_20140628_1724'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventhousing',
            name='person_avoid',
            field=models.TextField(verbose_name=b"I/We don't want to host", blank=True),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='person_prefer',
            field=models.TextField(verbose_name=b'I/We would love to host', blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='person_avoid',
            field=models.TextField(verbose_name=b"I/We don't want to host", blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='person_prefer',
            field=models.TextField(verbose_name=b'I/We would love to host', blank=True),
        ),
    ]
