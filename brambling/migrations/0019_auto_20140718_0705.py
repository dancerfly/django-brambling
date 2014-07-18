# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0018_auto_20140717_1827'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='liability_waiver',
            field=models.TextField(default='I hereby release <EVENT>, its officers, and its employees from all liability of injury, loss, or damage to personal property associated with this event. I acknowledge that I understand the content of this document. I am aware that it is legally binding and I accept it out of my own free will.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='attendee',
            name='liability_waiver',
            field=models.BooleanField(default=False, help_text=b'Must be checked by the attendee themselves'),
        ),
    ]
