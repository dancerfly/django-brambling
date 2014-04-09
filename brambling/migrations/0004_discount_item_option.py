# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0003_personitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='discount',
            name='item_option',
            field=models.ForeignKey(to='brambling.ItemOption', to_field=u'id'),
            preserve_default=True,
        ),
    ]
