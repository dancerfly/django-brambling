# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0004_discount_item_option'),
    ]

    operations = [
        migrations.AddField(
            model_name='discount',
            name='event',
            field=models.ForeignKey(to='brambling.Event', to_field=u'id'),
            preserve_default=True,
        ),
    ]
