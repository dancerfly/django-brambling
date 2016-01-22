# encoding: utf8
from __future__ import absolute_import, division, unicode_literals

import bleach
from bleach.callbacks import nofollow, target_blank
from django import template
from django.utils.safestring import mark_safe
import markdown
from markdown.extensions.smarty import SmartyExtension


register = template.Library()


class SkipImagesExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md, md_globals):
        del md.inlinePatterns['image_link']
        del md.inlinePatterns['image_reference']


md = markdown.Markdown(extensions=['markdown.extensions.nl2br',
                                   'markdown.extensions.sane_lists',
                                   SmartyExtension(smart_angled_quotes=True),
                                   SkipImagesExtension()],
                       output_format='html5')



@register.filter(name='markdown')
def markdown_filter(text):
    text = bleach.clean(text, strip=True)
    text = md.reset().convert(text)
    return mark_safe(bleach.linkify(text, [nofollow, target_blank]))
