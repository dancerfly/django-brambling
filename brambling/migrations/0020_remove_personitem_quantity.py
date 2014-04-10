# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0019_auto_20140409_1723'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='personitem',
            name='quantity',
        ),
    ]
