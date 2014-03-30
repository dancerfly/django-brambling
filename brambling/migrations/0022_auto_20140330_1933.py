# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0021_auto_20140330_1917'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='event_types',
            field=models.ManyToManyField(to='brambling.EventType', blank=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='dance_styles',
            field=models.ManyToManyField(to='brambling.DanceStyle', blank=True),
        ),
    ]
