# encoding: utf8
from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0029_auto_20140402_0433'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='created_timestamp',
            field=models.DateTimeField(default=datetime.datetime(2014, 4, 2, 5, 13, 43, 867504), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='itemoption',
            name='order',
            field=models.PositiveSmallIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='personitem',
            name='paid_at',
        ),
    ]
