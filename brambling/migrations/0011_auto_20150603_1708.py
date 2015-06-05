# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0010_auto_20150528_1805'),
    ]

    operations = [
        migrations.AddField(
            model_name='customformfield',
            name='choices',
            field=models.TextField(default='', help_text='Put each choice on its own line', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='customformfield',
            name='field_type',
            field=models.CharField(default='text', max_length=15, choices=[('text', 'Text'), ('textarea', 'Paragraph text'), ('boolean', 'Checkbox'), ('radio', 'Radio buttons'), ('select', 'Dropdown'), ('checkboxes', 'Multiple checkboxes'), ('select_multiple', 'Dropdown (Multiple)')]),
            preserve_default=True,
        ),
    ]
