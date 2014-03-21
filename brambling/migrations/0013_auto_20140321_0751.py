# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0012_dancestyle_eventtype'),
    ]

    operations = [
        migrations.AddField(
            model_name='dancestyle',
            name='related',
            field=models.ManyToManyField(to='brambling.DanceStyle', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='dance_style',
            field=models.ForeignKey(to_field=u'id', blank=True, to='brambling.DanceStyle', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='dance_style_other',
            field=models.CharField(default='', max_length=30, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='event_type',
            field=models.ForeignKey(to_field=u'id', blank=True, to='brambling.EventType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='event_type_other',
            field=models.CharField(default='', max_length=30, blank=True),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='event',
            name='category',
        ),
    ]
