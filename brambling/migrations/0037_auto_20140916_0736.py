# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0036_invite'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invite',
            name='status',
            field=models.CharField(default=b'unsent', max_length=8, choices=[(b'unsent', 'Unsent'), (b'sent', 'Sent'), (b'accepted', 'Accepted')]),
        ),
        migrations.AlterUniqueTogether(
            name='invite',
            unique_together=set([('email', 'content_id', 'kind')]),
        ),
    ]
