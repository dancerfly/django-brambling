# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0007_event_editors'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventhousing',
            name='home',
            field=models.ForeignKey(to='brambling.Home', to_field=u'id'),
            preserve_default=True,
        ),
    ]
