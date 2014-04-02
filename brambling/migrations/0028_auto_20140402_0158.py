# encoding: utf8
from django.db import models, migrations
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0027_auto_20140402_0157'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='EventHouseInfo',
            new_name='EventHouse'
        ),
    ]
