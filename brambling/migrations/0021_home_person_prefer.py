# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('brambling', '0020_home_person_avoid'),
    ]

    operations = [
        migrations.AddField(
            model_name='home',
            name='person_prefer',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name=b'I/We would love to host', blank=True),
            preserve_default=True,
        ),
    ]
