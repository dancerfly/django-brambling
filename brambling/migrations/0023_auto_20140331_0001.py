# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0022_auto_20140330_1933'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='collect_housing_data',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='item_reservation_length',
            field=models.PositiveSmallIntegerField(default=15),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='eventperson',
            name='wakeup',
            field=models.CharField(max_length=5, choices=[('late', u"I'll be up when I'm up"), ('early', u'There first thing.')]),
        ),
        migrations.AlterField(
            model_name='item',
            name='category',
            field=models.CharField(max_length=7, choices=[('merch', u'Merchandise'), ('comp', u'Competition'), ('class', u'Class/Lesson a la carte'), ('pass', u'Pass')]),
        ),
    ]
