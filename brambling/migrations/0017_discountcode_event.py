# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0016_discountcode_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='discountcode',
            name='event',
            field=models.ForeignKey(to='brambling.Event', default=1, to_field=u'id'),
            preserve_default=False,
        ),
    ]
