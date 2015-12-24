# encoding: utf8
from __future__ import absolute_import, division, unicode_literals

import bleach
from bleach.callbacks import nofollow, target_blank
from django import template
from django.utils.safestring import mark_safe
import markdown
from markdown.extensions.smarty import SmartyExtension


register = template.Library()
md = markdown.Markdown(extensions=['markdown.extensions.nl2br',
                                   'markdown.extensions.sane_lists',
                                   SmartyExtension(smart_angled_quotes=True)],
                       output_format='html5')


@register.filter(name='markdown')
def markdown_filter(text):
    text = bleach.linkify(bleach.clean(text, strip=True),
                          [nofollow, target_blank])
    return mark_safe(md.reset().convert(text))
