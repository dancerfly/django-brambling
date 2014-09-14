# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0028_itemimage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemoption',
            name='total_number',
            field=models.PositiveSmallIntegerField(help_text=b'Leave blank for unlimited.', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=models.DecimalField(max_digits=5, decimal_places=2, validators=[django.core.validators.MinValueValidator(0.01)]),
        ),
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(max_length=6, choices=[(b'stripe', b'Stripe'), (b'dwolla', b'Dwolla'), (b'cash', b'Cash'), (b'check', b'Check'), (b'fake', b'Fake')]),
        ),
        migrations.AlterField(
            model_name='subrefund',
            name='method',
            field=models.CharField(max_length=6, choices=[(b'stripe', b'Stripe'), (b'dwolla', b'Dwolla'), (b'cash', b'Cash'), (b'check', b'Check'), (b'fake', b'Fake')]),
        ),
    ]
