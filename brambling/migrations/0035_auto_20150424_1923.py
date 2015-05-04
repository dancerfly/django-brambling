# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0034_auto_20150424_1911'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Date',
            new_name='HousingRequestNight',
        ),
    ]
