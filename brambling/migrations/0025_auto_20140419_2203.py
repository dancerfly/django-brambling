# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        (b'brambling', b'0024_auto_20140414_0622'),
    ]

    operations = [
        migrations.AlterField(
            model_name=b'personitem',
            name=b'owner',
            field=models.ForeignKey(to_field='id', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
