# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0010_eventhousing_person_avoid'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventperson',
            name='person',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field=u'id'),
            preserve_default=True,
        ),
    ]
