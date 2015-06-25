# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0019_auto_20150528_1850'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='transfers_allowed',
            field=models.BooleanField(default=True, help_text='Whether user-to-user transfers are permitted.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='boughtitem',
            name='status',
            field=models.CharField(default='unpaid', max_length=8, choices=[('reserved', 'Reserved'), ('unpaid', 'Unpaid'), ('bought', 'Bought'), ('refunded', 'Refunded'), ('transferred', 'Transferred')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='invite',
            name='kind',
            field=models.CharField(max_length=10, choices=[('editor', 'Event Editor'), ('org_editor', 'Organization Editor'), ('transfer', 'Transfer')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(max_length=8, choices=[('purchase', 'Purchase'), ('refund', 'Refunded purchase'), ('transfer', 'Transfer'), ('other', 'Other')]),
            preserve_default=True,
        ),
    ]
