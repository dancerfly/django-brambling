# encoding: utf8
from __future__ import absolute_import, division, unicode_literals

import decimal

from django import template
from django.forms.widgets import CheckboxInput
from django.utils import timezone


register = template.Library()


CURRENCY_TO_SYMBOL = {
    'USD': ('$', 'left'),
    'GBP': ('£', 'left'),
}


@register.filter
def is_checkbox(field):
    return isinstance(field.field.widget, CheckboxInput)


@register.filter
def format_money(amount, currency):
    amount = decimal.Decimal(amount).quantize(decimal.Decimal('0.01'))
    if currency in CURRENCY_TO_SYMBOL:
        symbol, side = CURRENCY_TO_SYMBOL[currency]
        format = '{symbol}{amount}' if side == 'left' else '{amount}{symbol}'
        return format.format(symbol=symbol, amount=amount)
    return '{} {}'.format(amount, currency)


@register.filter
def absolute_value(value):
    try:
        return abs(value)
    except TypeError:
        return ''


@register.filter
def td_timeuntil(value, now=None):
    """
    Takes a datetime value and returns the timedelta between it and now.
    Optionally a second datetime value can be provided and it will return the
    difference between those two values.

    """

    if not now:
        now = timezone.localtime(timezone.now())

    try:
        td = value - now
    except TypeError:
        now = now.date()
        td = value - now

    return td


@register.assignment_tag
def td_to_dict(td):
    """
    Takes a timedelta and returns a dict with the following keys:

    * days
    * hours
    * minutes
    * seconds

    """

    return {
        'days': td.days,
        'hours': td.seconds // 3600 % 24,
        'minutes': td.seconds // 60 % 60,
        'seconds': td.seconds % 60,
    }


@register.filter
def pop_id(attrs):
    """
    Removes and returns 'id' from the passed-in dictionary, if present.
    """
    if 'id' in attrs:
        return attrs.pop('id')
