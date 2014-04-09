# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0005_discount_event'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='owner',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field=u'id'),
            preserve_default=True,
        ),
    ]
