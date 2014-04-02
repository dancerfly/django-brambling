# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0026_auto_20140402_0157'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventhouseinfo',
            name='nights',
            field=models.ManyToManyField(to='brambling.Date', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventperson',
            name='nights',
            field=models.ManyToManyField(to='brambling.Date', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='housingslot',
            name='nights',
            field=models.ManyToManyField(to='brambling.Date', null=True, blank=True),
            preserve_default=True,
        ),
    ]
