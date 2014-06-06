# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('brambling', '0005_attendee_event_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendee',
            name='person_prefer',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name=b'I need to be placed with', blank=True),
            preserve_default=True,
        ),
    ]
