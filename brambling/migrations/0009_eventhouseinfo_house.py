# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0008_event_editors'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventhouseinfo',
            name='house',
            field=models.ForeignKey(to='brambling.House', to_field=u'id'),
            preserve_default=True,
        ),
    ]
