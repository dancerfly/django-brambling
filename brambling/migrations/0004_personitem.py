# encoding: utf8
from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0003_eventhouseinfo_eventperson_house_housingslot_itemoption_payment_person_persondiscount'),
        #migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonItem',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('item_option', models.ForeignKey(to='brambling.ItemOption', to_field=u'id')),
                ('reserved', models.DateTimeField(default=django.utils.timezone.now)),
                ('paid_at', models.DateTimeField(null=True, blank=True)),
                ('paid_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field=u'id')),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field=u'id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
