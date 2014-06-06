# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0016_eventhousing_event_person'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='eventhousing',
            name='person_prefer',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name=b'I/We would love to host', blank=True),
            preserve_default=True,
        ),
    ]
