# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def forwards_func(apps, schema_editor):
    Attendee = apps.get_model('brambling', 'Attendee')
    Attendee.objects.filter(name_order='GMS').update(name_order='FML')
    Attendee.objects.filter(name_order='GS').update(name_order='FL')
    Attendee.objects.filter(name_order='SGM').update(name_order='LFM')
    Attendee.objects.filter(name_order='SG').update(name_order='LF')
    Person = apps.get_model('brambling', 'Person')
    Person.objects.filter(name_order='GMS').update(name_order='FML')
    Person.objects.filter(name_order='GS').update(name_order='FL')
    Person.objects.filter(name_order='SGM').update(name_order='LFM')
    Person.objects.filter(name_order='SG').update(name_order='LF')
    SavedAttendee = apps.get_model('brambling', 'SavedAttendee')    
    SavedAttendee.objects.filter(name_order='GMS').update(name_order='FML')
    SavedAttendee.objects.filter(name_order='GS').update(name_order='FL')
    SavedAttendee.objects.filter(name_order='SGM').update(name_order='LFM')
    SavedAttendee.objects.filter(name_order='SG').update(name_order='LF')
def reverse_func(apps, schema_editor):
    Attendee = apps.get_model('brambling', 'Attendee')
    Attendee.objects.filter(name_order='FML').update(name_order='GMS')
    Attendee.objects.filter(name_order='FL').update(name_order='GS')
    Attendee.objects.filter(name_order='LFM').update(name_order='SGM')
    Attendee.objects.filter(name_order='LF').update(name_order='SG')
    Person = apps.get_model('brambling', 'Person')
    Person.objects.filter(name_order='FML').update(name_order='GMS')
    Person.objects.filter(name_order='FL').update(name_order='GS')
    Person.objects.filter(name_order='LFM').update(name_order='SGM')
    Person.objects.filter(name_order='LF').update(name_order='SG')
    SavedAttendee = apps.get_model('brambling', 'SavedAttendee')    
    SavedAttendee.objects.filter(name_order='FML').update(name_order='GMS')
    SavedAttendee.objects.filter(name_order='FL').update(name_order='GS')
    SavedAttendee.objects.filter(name_order='LFM').update(name_order='SGM')
    SavedAttendee.objects.filter(name_order='LF').update(name_order='SG')
class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0044_auto_20160105_2012'),
    ]

    operations = [
	migrations.RunPython(forwards_func, reverse_func)
    ]
