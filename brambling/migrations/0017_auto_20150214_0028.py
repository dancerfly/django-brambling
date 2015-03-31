# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0016_auto_20150213_2009'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendee',
            name='housing_status',
            field=models.CharField(default=b'have', max_length=4, verbose_name=b'housing status', choices=[(b'need', b'Needs housing'), (b'have', b'Already arranged / hosting not required'), (b'home', b'Staying at own home')]),
            preserve_default=True,
        ),
    ]
