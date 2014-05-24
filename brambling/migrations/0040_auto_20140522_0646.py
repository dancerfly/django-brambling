# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0039_housingrequest'),
    ]

    operations = [
        migrations.CreateModel(
            name='HousingAssignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data', models.ForeignKey(to='brambling.HousingRequest', to_field='id')),
                ('slot', models.ForeignKey(to='brambling.HousingSlot', to_field='id')),
                ('assignment_type', models.CharField(max_length=6, choices=[(b'auto', 'Automatic'), (b'manual', 'Manual')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='housingslot',
            name='spaces_max',
            field=models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventhousing',
            name='point_person',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, default=1, to_field='id'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='eventperson',
            name='heard_through',
            field=models.CharField(default='', max_length=8, blank=True, choices=[(b'flyer', b'Flyer'), (b'facebook', b'Facebook'), (b'website', b'Event website'), (b'internet', b'Other website'), (b'friend', b'Friend'), (b'attendee', b'Former attendee'), (b'dancer', b'Other dancer'), (b'other', b'Other')]),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name='eventperson',
            old_name=b'housing',
            new_name='status',
        ),
        migrations.AddField(
            model_name='eventperson',
            name='heard_through_other',
            field=models.CharField(default='', max_length=128, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='housingslot',
            name='spaces',
            field=models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='housingslot',
            name='night',
            field=models.ForeignKey(to='brambling.Date', default=1, to_field='id'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='eventperson',
            name='liability_waiver',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventperson',
            name='send_flyers',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventperson',
            name='photos_ok',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='eventhousing',
            name=b'spaces_max',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name=b'person_avoid',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name=b'other_needs',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name=b'bedtime',
        ),
        migrations.RemoveField(
            model_name='eventhousing',
            name=b'spaces',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name=b'person_prefer',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name='ef_avoid_confirm',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name='ef_cause_confirm',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name=b'ef_avoid',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name=b'ef_cause',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name=b'housing_prefer',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name=b'car_spaces',
        ),
        migrations.RemoveField(
            model_name='housingslot',
            name=b'manual',
        ),
        migrations.RemoveField(
            model_name='housingslot',
            name=b'nights',
        ),
        migrations.RemoveField(
            model_name='eventhousing',
            name=b'nights',
        ),
        migrations.RemoveField(
            model_name='housingslot',
            name=b'person',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name=b'wakeup',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name=b'nights',
        ),
    ]
