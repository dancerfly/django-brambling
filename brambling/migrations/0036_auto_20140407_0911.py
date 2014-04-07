# encoding: utf8
from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0035_auto_20140407_0854'),
    ]

    operations = [
        migrations.CreateModel(
            name='Discount',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=40)),
                ('code', models.CharField(max_length=20)),
                ('item_option', models.ForeignKey(to='brambling.ItemOption', to_field=u'id')),
                ('available_start', models.DateTimeField(null=True, blank=True)),
                ('available_end', models.DateTimeField(null=True, blank=True)),
                ('discount_type', models.CharField(default='percent', max_length=7, choices=[('percent', u'Percent'), ('flat', u'Flat')])),
                ('amount', models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)])),
                ('event', models.ForeignKey(to='brambling.Event', to_field=u'id')),
            ],
            options={
                u'unique_together': set([('code', 'event')]),
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='event',
            name='reservation_timeout',
            field=models.PositiveSmallIntegerField(default=15, help_text='Minutes before reserved items are removed from cart.'),
        ),
    ]
