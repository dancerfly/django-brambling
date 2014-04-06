# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0033_auto_20140406_1742'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='reservation_timeout',
            field=models.PositiveSmallIntegerField(default=15, help_text='Minutes before items bought are removed from cart.'),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='event',
            name='item_reservation_length',
        ),
    ]
