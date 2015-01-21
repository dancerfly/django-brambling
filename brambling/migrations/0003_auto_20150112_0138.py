# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0002_auto_20141222_0851'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='subpayment',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='subpayment',
            name='bought_item',
        ),
        migrations.RemoveField(
            model_name='subpayment',
            name='payment',
        ),
        migrations.RemoveField(
            model_name='subrefund',
            name='refund',
        ),
        migrations.RemoveField(
            model_name='subrefund',
            name='subpayment',
        ),
        migrations.DeleteModel(
            name='SubRefund',
        ),
        migrations.RemoveField(
            model_name='boughtitem',
            name='payments',
        ),
        migrations.DeleteModel(
            name='SubPayment',
        ),
        migrations.RemoveField(
            model_name='refund',
            name='bought_item',
        ),
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(default='in_progress', max_length=11, choices=[(b'in_progress', 'In progress'), (b'completed', 'Completed'), (b'refunded', 'Refunded')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='refund',
            name='method',
            field=models.CharField(default='fake', max_length=6, choices=[(b'stripe', b'Stripe'), (b'dwolla', b'Dwolla'), (b'cash', b'Cash'), (b'check', b'Check'), (b'fake', b'Fake')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='refund',
            name='payment',
            field=models.ForeignKey(related_name=b'refunds', default=1, to='brambling.Payment'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='refund',
            name='remote_id',
            field=models.CharField(default='', max_length=40, blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='boughtitem',
            name='status',
            field=models.CharField(default=b'unpaid', max_length=8, choices=[(b'reserved', 'Reserved'), (b'unpaid', 'Unpaid'), (b'paid', 'Paid'), (b'bought', 'Bought'), (b'refunded', 'Refunded')]),
        ),
    ]
