# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0008_auto_20150128_2208'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='application_fee',
            field=models.DecimalField(default=0, max_digits=5, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='transaction',
            name='created_by',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='transaction',
            name='processing_fee',
            field=models.DecimalField(default=0, max_digits=5, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='transaction',
            name='related_transaction',
            field=models.ForeignKey(blank=True, to='brambling.Transaction', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(default='purchase', max_length=5, choices=[(b'purchase', 'Purchase'), (b'refund', 'Refunded purchase'), (b'other', 'Other')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='amount',
            field=models.DecimalField(default=0, max_digits=5, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='method',
            field=models.CharField(max_length=7, choices=[(b'stripe', b'Stripe'), (b'dwolla', b'Dwolla'), (b'cash', b'Cash'), (b'check', b'Check'), (b'fake', b'Fake')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='order',
            field=models.ForeignKey(related_name='transactions', blank=True, to='brambling.Order', null=True),
            preserve_default=True,
        ),
    ]
