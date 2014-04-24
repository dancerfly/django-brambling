# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        (b'brambling', b'0027_auto_20140423_2344'),
    ]

    operations = [
        migrations.AlterField(
            model_name=b'eventperson',
            name=b'housing',
            field=models.CharField(default=b'have', max_length=4, choices=[(b'need', b'Need housing'), (b'have', b'Already arranged'), (b'host', b'Hosting others')]),
        ),
        migrations.AlterField(
            model_name=b'eventperson',
            name=b'event_pass',
            field=models.OneToOneField(to=b'brambling.PersonItem', to_field='id'),
        ),
    ]
