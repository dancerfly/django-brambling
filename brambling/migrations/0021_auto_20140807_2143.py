# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0020_auto_20140807_2104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendee',
            name='person_avoid',
            field=models.TextField(help_text=b'Provide a list of names, separated by line breaks.', verbose_name=b'I do not want to be around these people', blank=True),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='person_prefer',
            field=models.TextField(help_text=b'Provide a list of names, separated by line breaks.', verbose_name=b'I need to be placed with these people', blank=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='liability_waiver',
            field=models.TextField(default='I hereby release {event}, its officers, and its employees from all liability of injury, loss, or damage to personal property associated with this event. I acknowledge that I understand the content of this document. I am aware that it is legally binding and I accept it out of my own free will.', help_text="'{event}' will be automatically replaced with your event name when users are presented with the waiver."),
        ),
    ]
