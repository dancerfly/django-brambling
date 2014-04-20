# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        (b'brambling', b'0025_auto_20140419_2203'),
    ]

    operations = [
        migrations.AddField(
            model_name=b'eventperson',
            name=b'event_pass',
            field=models.ForeignKey(to=b'brambling.ItemOption', default=1, to_field='id'),
            preserve_default=False,
        ),
    ]
