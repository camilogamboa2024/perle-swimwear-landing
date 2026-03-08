from django import template

from apps.orders.money import cents_to_usd_decimal, format_usd

register = template.Library()


@register.filter
def usd(value):
    return format_usd(value)


@register.filter
def usd_decimal(value):
    return f'{cents_to_usd_decimal(value):,.2f}'
