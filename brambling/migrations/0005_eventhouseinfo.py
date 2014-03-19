# encoding: utf8
from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0004_house'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventHouseInfo',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('event', models.ForeignKey(to='brambling.Event', to_field=u'id')),
                ('house', models.ForeignKey(to='brambling.House', to_field=u'id')),
                ('spaces', models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)])),
                ('nights', models.CommaSeparatedIntegerField(max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
