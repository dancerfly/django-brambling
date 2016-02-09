# encoding: utf8
from __future__ import absolute_import, division, unicode_literals

from django import template


register = template.Library()


@register.filter
def ljust(string, width, fillchar=' '):
    try:
        return string.ljust(width, fillchar)
    except (AttributeError, TypeError):
        return ''
