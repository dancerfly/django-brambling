# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def permissions_forward(apps, schema_editor):
    EventMember = apps.get_model('brambling', 'EventMember')
    OrganizationMember = apps.get_model('brambling', 'OrganizationMember')
    Event = apps.get_model('brambling', 'Event')
    Organization = apps.get_model('brambling', 'Organization')
    Invite = apps.get_model('brambling', 'Invite')

    eventmembers = []
    for event in Event.objects.prefetch_related('additional_editors'):
        for person in event.additional_editors.all():
            eventmembers.append(EventMember(person=person, event=event, role='1-edit'))
    EventMember.objects.bulk_create(eventmembers)

    organizationmembers = []
    for organization in Organization.objects.prefetch_related('editors').select_related('owner'):
        organizationmembers.append(OrganizationMember(person=organization.owner, organization=organization, role='0-owner'))
        for person in organization.editors.all():
            # Some orgs could hypothetically have an owner also as an editor.
            if person != organization.owner:
                organizationmembers.append(OrganizationMember(person=person, organization=organization, role='1-edit'))
    OrganizationMember.objects.bulk_create(organizationmembers)

    Invite.objects.filter(kind='editor').update(kind='event_edit')
    Invite.objects.filter(kind='org_editor').update(kind='org_edit')


def permissions_backward(apps, schema_editor):
    EventMember = apps.get_model('brambling', 'EventMember')
    OrganizationMember = apps.get_model('brambling', 'OrganizationMember')
    Invite = apps.get_model('brambling', 'Invite')

    for member in EventMember.objects.filter(role='1-edit').select_related('event', 'person'):
        member.event.additional_editors.add(member.person)
    for member in OrganizationMember.objects.filter(role='1-edit').select_related('organization', 'person'):
        member.organization.editors.add(member.person)
    for member in OrganizationMember.objects.filter(role='0-owner').select_related('person'):
        if member.organization.owner_id is None:
            member.organization.owner = member.person
            member.organization.save()
        else:
            member.organization.editors.add(member.person)

    Invite.objects.filter(kind='event_edit').update(kind='editor')
    Invite.objects.filter(kind='org_edit').update(kind='org_editor')
    Invite.objects.filter(kind='event_view').delete()
    Invite.objects.filter(kind='org_view').delete()
    Invite.objects.filter(kind='org_owner').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0046_auto_20160131_0109'),
    ]

    operations = [
        migrations.RunPython(permissions_forward, permissions_backward),
    ]
