# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def single_name_field_to_multiple(apps, schema_editor):
    """
    Naively attempts to split single names into multiple names.
    Running this on a live database is not advisable since it does not account
    for names which do not follow a "First Middle Last" structure.

    """
    Person = apps.get_model("brambling", "Person")
    for person in Person.objects.all():

        # Convert single to separated name:
        name_bits = person.name.split(" ")
        if len(name_bits) < 2:
            person.given_name = name_bits[0]
            person.surname = "NO SURNAME"
        elif len(name_bits) == 2:
            person.given_name = name_bits[0]
            person.surname = name_bits[1]
        elif len(name_bits) > 2:
            person.given_name = name_bits[0]
            person.middle_name = name_bits[1]
            person.surname = " ".join(name_bits[2:])

        # Save
        person.save()


def multiple_name_to_single_field(apps, schema_editor):
    """
    Converts multiple names to a single name.
    Naively joins first, middle, and last names with a space.

    """
    Person = apps.get_model("brambling", "Person")
    for person in Person.objects.all():

        # Convert multiple names to a single name:
        name_bits = [person.first_name]
        if person.middle_name != "" and person.name_order in ("SGM", "GMS"):
            name_bits.append(person.middle_name)
        if person.surname != "NO SURNAME":
            if person.name_order in ("SG", "SGM"):
                name_bits.insert(0, person.surname)
            else:
                name_bits.append(person.surname)
        person.name = " ".join

        # Save
        person.save()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0013_auto_20140715_2225'),
    ]

    operations = [
        migrations.RunPython(single_name_field_to_multiple, multiple_name_to_single_field),
    ]
