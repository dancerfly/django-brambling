# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0025_auto_20140331_0725'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventhouseinfo',
            name='nights',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name='nights',
        ),
        migrations.RemoveField(
            model_name='housingslot',
            name='nights',
        ),
    ]
