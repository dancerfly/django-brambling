# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0020_auto_20140324_0612'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='person',
            name='all_event_types',
        ),
        migrations.RemoveField(
            model_name='person',
            name='all_dance_styles',
        ),
        migrations.AlterField(
            model_name='person',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Full name'),
        ),
    ]
