from django import template
import re
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def highlight(text, query):
    if not query:
        return text
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    highlighted = pattern.sub(
        lambda match: f'<mark style="background-color: #fff3cd; padding: 0 2px;">{match.group(0)}</mark>',
        text
    )
    return mark_safe(highlighted)
