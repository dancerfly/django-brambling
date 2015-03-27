# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def organizations_create(apps, schema_editor):
    Organization = apps.get_model("brambling", "Organization")
    Event = apps.get_model("brambling", "Event")

    # Orgs that don't exist should be created with some default info
    # and all the permissions / payment stuff that is about to be
    # removed from events.
    for event in Event.objects.all():
        if event.organization_id:
            continue
        org = Organization.objects.create(
            name=event.name,
            slug=event.slug,
            city=event.city,
            state_or_province=event.state_or_province,
            country=event.country,
            owner=event.owner,
            stripe_user_id=event.stripe_user_id,
            stripe_access_token=event.stripe_access_token,
            stripe_refresh_token=event.stripe_refresh_token,
            stripe_publishable_key=event.stripe_publishable_key,
            stripe_test_user_id=event.stripe_test_user_id,
            stripe_test_access_token=event.stripe_test_access_token,
            stripe_test_refresh_token=event.stripe_test_refresh_token,
            stripe_test_publishable_key=event.stripe_test_publishable_key,
            default_application_fee_percent=event.application_fee_percent,
            check_payment_allowed=event.check_payment_allowed,
            check_payable_to=event.check_payable_to,
            check_postmark_cutoff=event.check_postmark_cutoff,
            check_recipient=event.check_recipient,
            check_address=event.check_address,
            check_address_2=event.check_address_2,
            check_city=event.check_city,
            check_state_or_province=event.check_state_or_province,
            check_zip=event.check_zip,
            check_country=event.check_country,
        )

        org.dance_styles = event.dance_styles.all()
        org.editors = event.editors.all()
        event.organization = org
        event.save()


def organizations_destroy(apps, schema_editor):
    Organization = apps.get_model("brambling", "Organization")
    Event = apps.get_model("brambling", "Event")
    if Organization.objects.annotate(event_count=models.Count("event")).exclude(event_count=1):
        raise Exception("Cannot automigrate backwards - data would be badly corrupted.")

    # Transfer back any permissions / payment data that was lost.
    for event in Event.objects.all():
        if not event.organization_id:
            continue
        event.owner = event.organization.owner
        event.stripe_user_id = event.organization.stripe_user_id
        event.stripe_access_token = event.organization.stripe_access_token
        event.stripe_refresh_token = event.organization.stripe_refresh_token
        event.stripe_publishable_key = event.organization.stripe_publishable_key
        event.stripe_test_user_id = event.organization.stripe_test_user_id
        event.stripe_test_access_token = event.organization.stripe_test_access_token
        event.stripe_test_refresh_token = event.organization.stripe_test_refresh_token
        event.stripe_test_publishable_key = event.organization.stripe_test_publishable_key
        event.check_payment_allowed = event.organization.check_payment_allowed
        event.check_payable_to = event.organization.check_payable_to
        event.check_postmark_cutoff = event.organization.check_postmark_cutoff
        event.check_recipient = event.organization.check_recipient
        event.check_address = event.organization.check_address
        event.check_address_2 = event.organization.check_address_2
        event.check_city = event.organization.check_city
        event.check_state_or_province = event.organization.check_state_or_province
        event.check_zip = event.organization.check_zip
        event.check_country = event.organization.check_country

        event.editors = event.organization.editors.all()
        event.organization = None
        event.save()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0026_auto_20150327_2139'),
    ]

    operations = [
        migrations.RunPython(organizations_create,
                             organizations_destroy),
    ]
