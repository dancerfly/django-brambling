# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0030_auto_20150421_2121'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discount',
            name='amount',
            field=models.DecimalField(verbose_name='discount value', max_digits=5, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='liability_waiver',
            field=models.TextField(default='I hereby release {organization}, its officers, and its employees from all liability of injury, loss, or damage to personal property associated with this event. I acknowledge that I understand the content of this document. I am aware that it is legally binding and I accept it out of my own free will.', help_text="'{event}' and '{organization}' will be automatically replaced with your event and organization names respectively when users are presented with the waiver."),
            preserve_default=True,
        ),
    ]
