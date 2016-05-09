from django import template
from django.utils.encoding import force_text

register = template.Library()

@register.filter
def to_string(val):
    return force_text(val)
