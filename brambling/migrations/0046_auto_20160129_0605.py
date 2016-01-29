# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def permissions_forward(apps, schema_editor):
    EventMember = apps.get_model('brambling', 'EventMember')
    OrganizationMember = apps.get_model('brambling', 'OrganizationMember')
    Event = apps.get_model('brambling', 'Event')
    Organization = apps.get_model('brambling', 'Organization')
    Invite = apps.get_model('brambling', 'Invite')

    eventmembers = []
    for event in Event.objects.prefetch_related('additional_editors'):
        for person in event.additional_editors.all():
            eventmembers.append(EventMember(person=person, event=event, role='edit'))
    EventMember.objects.bulk_create(eventmembers)

    organizationmembers = []
    for organization in Organization.objects.prefetch_related('editors'):
        for person in organization.editors.all():
            organizationmembers.append(OrganizationMember(person=person, organization=organization, role='edit'))
    OrganizationMember.objects.bulk_create(organizationmembers)

    Invite.objects.filter(kind='editor').update(kind='event_edit')
    Invite.objects.filter(kind='org_editor').update(kind='org_edit')


def permissions_backward(apps, schema_editor):
    EventMember = apps.get_model('brambling', 'EventMember')
    OrganizationMember = apps.get_model('brambling', 'OrganizationMember')
    Invite = apps.get_model('brambling', 'Invite')

    for member in EventMember.objects.filter(role='edit').select_related('event', 'person'):
        member.event.additional_editors.add(member.person)
    for member in OrganizationMember.objects.filter(role='edit').select_related('organization', 'person'):
        member.organization.editors.add(member.person)

    Invite.objects.filter(kind='event_edit').update(kind='editor')
    Invite.objects.filter(kind='org_edit').update(kind='org_editor')
    Invite.objects.filter(kind='event_view').delete()
    Invite.objects.filter(kind='org_view').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0045_auto_20160129_0604'),
    ]

    operations = [
        migrations.RunPython(permissions_forward, permissions_backward),
    ]
