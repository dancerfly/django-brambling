# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def create(person, SavedAttendee):
    saved = SavedAttendee.objects.create(
        person=person,
        given_name=person.given_name,
        middle_name=person.middle_name,
        surname=person.surname,
        name_order=person.name_order,
        person_prefer=person.person_prefer,
        person_avoid=person.person_avoid,
        other_needs=person.other_needs,
    )
    saved.ef_cause = person.ef_cause.all()
    saved.ef_avoid = person.ef_avoid.all()
    saved.housing_prefer = person.housing_prefer.all()


def should_create_for(person):
    if person.other_needs or person.person_prefer or person.person_avoid:
        return True
    if person.ef_cause.all() or person.ef_avoid.all() or person.housing_prefer.all():
        return True
    return False


def create_saved_attendees(apps, schema_editor):
    SavedAttendee = apps.get_model('brambling', 'SavedAttendee')
    Person = apps.get_model('brambling', 'Person')

    people = Person.objects.prefetch_related(
        'ef_cause',
        'ef_avoid',
        'housing_prefer',
    )

    for person in people:
        if should_create_for(person):
            create(person, SavedAttendee)


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0026_savedattendee'),
    ]

    operations = [
        migrations.RunPython(create_saved_attendees, lambda *a, **k: None)
    ]
