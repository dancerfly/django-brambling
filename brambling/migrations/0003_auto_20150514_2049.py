# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0002_auto_20150502_0912'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invite',
            name='kind',
            field=models.CharField(max_length=10, choices=[('editor', 'Event Editor'), ('org_editor', 'Organization Editor')]),
            preserve_default=True,
        ),
    ]
