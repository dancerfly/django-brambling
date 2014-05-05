# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        (b'brambling', b'0029_auto_20140424_0729'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name=b'persondiscount',
            unique_together=set([(b'person', b'discount')]),
        ),
    ]
