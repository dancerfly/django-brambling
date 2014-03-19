# encoding: utf8
from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0008_auto_20140319_1659'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscountCode',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=20)),
                ('available_start', models.DateTimeField()),
                ('available_end', models.DateTimeField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ItemDiscount',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('item', models.ForeignKey(to='brambling.Item', to_field=u'id')),
                ('discount', models.ForeignKey(to='brambling.DiscountCode', to_field=u'id')),
                ('discount_type', models.CharField(default='percent', max_length=7, choices=[('percent', u'Percent'), ('flat', u'Flat')])),
                ('amount', models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
