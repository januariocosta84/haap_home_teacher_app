from django import template

register = template.Library()

@register.filter
def split_dash(value, index):
    if value:
        parts = value.split('-')
        try:
            return parts[int(index)].strip()
        except:
            return ''
    return ''