# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0017_auto_20140717_1818'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='order',
            unique_together=set([(b'event', b'code')]),
        ),
    ]
