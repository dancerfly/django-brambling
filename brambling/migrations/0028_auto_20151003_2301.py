# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0027_saved_attendee_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='savedattendee',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2015, 10, 3, 23, 1, 14, 80632, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='savedattendee',
            name='last_modified',
            field=models.DateTimeField(default=datetime.datetime(2015, 10, 3, 23, 1, 18, 111276, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
