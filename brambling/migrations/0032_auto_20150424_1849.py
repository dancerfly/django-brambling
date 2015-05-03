# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime

from django.db import models, migrations


def dates_forward(apps, schema_editor):
    Event = apps.get_model("brambling", "Event")
    HousingSlot = apps.get_model("brambling", "HousingSlot")
    events = Event.objects.annotate(
        start_date_=models.Min('dates__date'),
        end_date_=models.Max('dates__date')
    )

    for event in events:
        event.start_date = event.start_date_
        event.end_date = event.end_date_
        event.save()

    for slot in HousingSlot.objects.select_related('night'):
        slot.date = slot.night.date
        slot.save()


def dates_backward(apps, schema_editor):
    Event = apps.get_model("brambling", "Event")
    HousingSlot = apps.get_model("brambling", "HousingSlot")
    Date = apps.get_model("brambling", "Date")

    for slot in HousingSlot.objects.all():
        slot.night = Date.objects.get_or_create(date=slot.date)[0]
        slot.save()

    for event in Event.objects.all():
        date_set = {event.start_date + datetime.timedelta(n - 1) for n in
                    xrange((event.end_date - event.start_date).days + 2)}
        seen = set(Date.objects.filter(date__in=date_set
                                       ).values_list('date', flat=True))
        Date.objects.bulk_create([
            Date(date=date) for date in date_set
            if date not in seen
        ])
        event.housing_dates = Date.objects.filter(date__in=date_set)
        date_set.remove(event.start_date - datetime.timedelta(1))
        event.dates = Date.objects.filter(date__in=date_set)


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0031_auto_20150424_1848'),
    ]

    operations = [
        migrations.RunPython(dates_forward, dates_backward)
    ]
