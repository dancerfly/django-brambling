# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0029_auto_20140910_1902'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='banner_image',
            field=models.ImageField(default='', upload_to=b'', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='logo_image',
            field=models.ImageField(default='', upload_to=b'', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='website_url',
            field=models.URLField(default='', blank=True),
            preserve_default=False,
        ),
    ]
