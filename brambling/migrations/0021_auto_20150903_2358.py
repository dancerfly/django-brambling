# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0020_auto_20150609_0033'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='transfers_allowed',
            field=models.BooleanField(default=True, help_text='Whether users can transfer items directly to other users.'),
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
            field=models.CharField(max_length=10, choices=[('event', 'Event'), ('editor', 'Event Editor'), ('org_editor', 'Organization Editor'), ('transfer', 'Transfer')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='invite',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='method',
            field=models.CharField(max_length=7, choices=[('stripe', 'Stripe'), ('dwolla', 'Dwolla'), ('cash', 'Cash'), ('check', 'Check'), ('fake', 'Fake'), ('none', 'No balance change')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(max_length=8, choices=[('purchase', 'Purchase'), ('refund', 'Refunded purchase'), ('transfer', 'Transfer'), ('other', 'Other')]),
            preserve_default=True,
        ),
    ]
