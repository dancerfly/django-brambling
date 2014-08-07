# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0019_auto_20140718_0705'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendee',
            name='liability_waiver',
            field=models.BooleanField(default=False, help_text=b'Must be agreed to by the attendee themselves.'),
        ),
    ]
