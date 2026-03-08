from decimal import Decimal, ROUND_HALF_UP

COP_TO_USD_RATE = Decimal('0.00026')
HUNDRED = Decimal('100')


def cop_to_usd_cents(value):
    if value is None:
        return None
    cents = (Decimal(value) * COP_TO_USD_RATE * HUNDRED).quantize(
        Decimal('1'),
        rounding=ROUND_HALF_UP,
    )
    return int(cents)


def usd_to_cents(value):
    if value is None:
        return None
    cents = (Decimal(value) * HUNDRED).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return int(cents)


def cents_to_usd_decimal(value):
    cents = int(value or 0)
    return (Decimal(cents) / HUNDRED).quantize(Decimal('0.01'))


def format_usd(value):
    amount = cents_to_usd_decimal(value)
    return f'USD {amount:,.2f}'
