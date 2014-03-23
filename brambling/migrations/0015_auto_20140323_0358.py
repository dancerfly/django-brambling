# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0014_auto_20140322_1838'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemoption',
            name='name',
            field=models.CharField(max_length=30),
        ),
    ]
