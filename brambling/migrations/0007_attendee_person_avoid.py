# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0006_attendee_person_prefer'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='attendee',
            name='person_avoid',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name=b'I do not want to be around', blank=True),
            preserve_default=True,
        ),
    ]
