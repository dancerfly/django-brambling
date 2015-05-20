# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0007_savedreport'),
    ]

    operations = [
        migrations.RenameField(
            model_name='item',
            old_name='created_timestamp',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='person',
            old_name='created_timestamp',
            new_name='created',
        ),
        migrations.AddField(
            model_name='event',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2015, 5, 20, 2, 53, 14, 945519, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='item',
            name='last_modified',
            field=models.DateTimeField(default=datetime.datetime(2015, 5, 20, 2, 53, 18, 505307, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='organization',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2015, 5, 20, 2, 53, 25, 97114, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='organization',
            name='last_modified',
            field=models.DateTimeField(default=datetime.datetime(2015, 5, 20, 2, 53, 28, 566674, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='person',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2015, 5, 20, 2, 53, 35, 392219, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='person',
            name='last_modified',
            field=models.DateTimeField(default=datetime.datetime(2015, 5, 20, 2, 53, 40, 759961, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
