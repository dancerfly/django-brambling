# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0045_auto_20160104_2208'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(max_length=6, choices=[('1-edit', 'Can edit event'), ('2-view', 'Can view event')])),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('event', models.ForeignKey(to='brambling.Event')),
                ('person', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrganizationMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(max_length=7, choices=[('0-owner', 'Is organization owner'), ('1-edit', 'Can edit organization'), ('2-view', 'Can view organization')])),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(to='brambling.Organization')),
                ('person', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='organizationmember',
            unique_together=set([('organization', 'person')]),
        ),
        migrations.AlterUniqueTogether(
            name='eventmember',
            unique_together=set([('event', 'person')]),
        ),
        migrations.AddField(
            model_name='event',
            name='members',
            field=models.ManyToManyField(related_name='events', null=True, through='brambling.EventMember', to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='organization',
            name='members',
            field=models.ManyToManyField(related_name='organizations', null=True, through='brambling.OrganizationMember', to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='invite',
            name='kind',
            field=models.CharField(max_length=10, choices=[('event', 'Event'), ('event_edit', 'Edit event'), ('event_view', 'View event'), ('org_edit', 'Edit organization'), ('org_view', 'View organization'), ('transfer', 'Transfer')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='organization',
            name='owner',
            field=models.ForeignKey(related_name='owner_orgs', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
