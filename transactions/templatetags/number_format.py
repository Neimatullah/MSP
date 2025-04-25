from django import template

register = template.Library()

@register.filter
def format_number(value):
    return "{:,}".format(value)
