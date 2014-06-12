# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0023_auto_20140606_1954'),
    ]

    operations = [
        migrations.AlterField(
            model_name='boughtitem',
            name='attendee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to_field='id', blank=True, to='brambling.Attendee', null=True),
        ),
        migrations.AlterField(
            model_name='discount',
            name='discount_type',
            field=models.CharField(default=b'flat', max_length=7, choices=[(b'flat', 'Flat'), (b'percent', 'Percent')]),
        ),
        migrations.AlterField(
            model_name='event',
            name='slug',
            field=models.SlugField(help_text=b'URL-friendly version of the event name. Dashes, 0-9, and lower-case a-z only.', unique=True, validators=[django.core.validators.RegexValidator(b'[a-z0-9-]+')]),
        ),
    ]
