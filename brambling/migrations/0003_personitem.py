# encoding: utf8
from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0002_eventhousing_eventperson_home_housingslot_itemoption_payment_person_persondiscount'),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonItem',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('item_option', models.ForeignKey(to='brambling.ItemOption', to_field=u'id')),
                ('quantity', models.PositiveSmallIntegerField()),
                ('added', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(default='unpaid', max_length=8, choices=[('reserved', u'Reserved'), ('unpaid', u'Unpaid'), ('partial', u'Partially paid'), ('paid', u'Paid')])),
                ('buyer', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field=u'id')),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field=u'id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
