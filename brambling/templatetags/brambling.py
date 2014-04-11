from __future__ import absolute_import

from django import template
from django.forms.widgets import CheckboxInput


register = template.Library()


@register.filter
def is_checkbox(field):
    return isinstance(field.field.widget, CheckboxInput)
