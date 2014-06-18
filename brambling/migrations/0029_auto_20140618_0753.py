# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0028_auto_20140618_0752'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendee',
            name='person_avoid',
            field=models.TextField(default='', verbose_name=b'I do not want to be around', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='attendee',
            name='person_prefer',
            field=models.TextField(default='', verbose_name=b'I need to be placed with', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='eventhousing',
            name='person_avoid',
            field=models.TextField(default='', help_text=b'Include resident preferences', verbose_name=b"I/We don't want to host", blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='eventhousing',
            name='person_prefer',
            field=models.TextField(default='', help_text=b'Include resident preferences', verbose_name=b'I/We would love to host', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='home',
            name='person_avoid',
            field=models.TextField(default='', help_text=b'Include resident preferences', verbose_name=b"I/We don't want to host", blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='home',
            name='person_prefer',
            field=models.TextField(default='', help_text=b'Include resident preferences', verbose_name=b'I/We would love to host', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='person',
            name='person_avoid',
            field=models.TextField(default='', verbose_name=b'I do not want to be around', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='person',
            name='person_prefer',
            field=models.TextField(default='', verbose_name=b'I need to be placed with', blank=True),
            preserve_default=False,
        ),
    ]
