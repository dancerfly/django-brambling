# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('brambling', '0022_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomForm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('form_type', models.CharField(max_length=8, choices=[('attendee', 'Attendee'), ('order', 'Order')])),
                ('name', models.CharField(max_length=50)),
                ('index', models.PositiveSmallIntegerField(default=0)),
                ('event', models.ForeignKey(to='brambling.Event', related_name='forms')),
            ],
            options={
                'ordering': ('index',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomFormEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('related_id', models.IntegerField()),
                ('value', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CustomFormField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field_type', models.CharField(default='text', max_length=8, choices=[('text', 'Text'), ('textarea', 'Paragraph text'), ('boolean', 'Checkbox')])),
                ('name', models.CharField(max_length=30)),
                ('default', models.CharField(max_length=255, blank=True)),
                ('required', models.BooleanField(default=False)),
                ('index', models.PositiveSmallIntegerField(default=0)),
                ('form', models.ForeignKey(related_name='fields', to='brambling.CustomForm')),
            ],
            options={
                'ordering': ('index',),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='customformentry',
            name='form_field',
            field=models.ForeignKey(to='brambling.CustomFormField'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customformentry',
            name='related_ct',
            field=models.ForeignKey(to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='customformentry',
            unique_together=set([('related_ct', 'related_id', 'form_field')]),
        ),
        migrations.AlterField(
            model_name='discount',
            name='code',
            field=models.CharField(help_text='Allowed characters: 0-9, a-z, A-Z, space, and \'"~+=', max_length=20, validators=[django.core.validators.RegexValidator('^[0-9A-Za-z \'"~+=]+$')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='slug',
            field=models.SlugField(help_text='URL-friendly version of the event name. Dashes, 0-9, and lower-case a-z only.', unique=True, validators=[django.core.validators.RegexValidator('^[a-z0-9-]+$')]),
            preserve_default=True,
        ),
    ]
