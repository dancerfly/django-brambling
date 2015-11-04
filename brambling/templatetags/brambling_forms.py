# encoding: utf8
from __future__ import absolute_import, division, unicode_literals

from django import template


register = template.Library()


@register.filter
def get_value(form, field):
    return form._raw_value(field)
