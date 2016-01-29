# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0046_auto_20160129_0605'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventmember',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2016, 1, 29, 6, 10, 59, 638039, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='eventmember',
            name='last_modified',
            field=models.DateTimeField(default=datetime.datetime(2016, 1, 29, 6, 11, 6, 235770, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='organizationmember',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2016, 1, 29, 6, 11, 12, 465831, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='organizationmember',
            name='last_modified',
            field=models.DateTimeField(default=datetime.datetime(2016, 1, 29, 6, 11, 15, 361722, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
