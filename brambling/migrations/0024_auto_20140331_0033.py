# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0023_auto_20140331_0001'),
    ]

    operations = [
        migrations.RenameField(
            model_name='personitem',
            old_name='paid_by',
            new_name='buyer',
        ),
    ]
