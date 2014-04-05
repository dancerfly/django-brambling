# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0028_auto_20140402_0158'),
    ]

    operations = [
        migrations.AddField(
            model_name='personitem',
            name='status',
            field=models.CharField(default='unpaid', max_length=8, choices=[('reserved', u'Reserved'), ('unpaid', u'Unpaid'), ('partial', u'Partially paid'), ('paid', u'Paid')]),
            preserve_default=True,
        ),
        migrations.RenameField(
            model_name='personitem',
            old_name='reserved',
            new_name='added',
        ),
        migrations.AddField(
            model_name='personitem',
            name='quantity',
            field=models.PositiveSmallIntegerField(default=1),
            preserve_default=False,
        ),
    ]
