# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0021_auto_20150903_2358'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='slug',
            field=models.SlugField(help_text='URL-friendly version of the event name. Dashes, 0-9, and lower-case a-z only.', validators=[django.core.validators.RegexValidator('^[a-z0-9-]+$')]),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='event',
            unique_together=set([('slug', 'organization')]),
        ),
    ]
