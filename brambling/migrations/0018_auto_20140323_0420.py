# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0017_discountcode_event'),
    ]

    operations = [
        migrations.CreateModel(
            name='Discount',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=40)),
                ('code', models.CharField(max_length=20)),
                ('available_start', models.DateTimeField()),
                ('available_end', models.DateTimeField()),
                ('event', models.ForeignKey(to='brambling.Event', to_field=u'id')),
                ('items', models.ManyToManyField(to='brambling.Item', through='brambling.ItemDiscount')),
            ],
            options={
                u'unique_together': set([('code', 'event')]),
            },
            bases=(models.Model,),
        ),
        migrations.DeleteModel(
            name='DiscountCode',
        ),
        migrations.AlterField(
            model_name='userdiscount',
            name='discount',
            field=models.ForeignKey(to='brambling.Discount', to_field=u'id'),
        ),
        migrations.AlterField(
            model_name='itemdiscount',
            name='discount',
            field=models.ForeignKey(to='brambling.Discount', to_field=u'id'),
        ),
    ]
