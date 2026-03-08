from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations, models

COP_TO_USD_RATE = Decimal('0.00026')
HUNDRED = Decimal('100')


def _cop_to_usd_cents(value):
    cents = (Decimal(value) * COP_TO_USD_RATE * HUNDRED).quantize(
        Decimal('1'),
        rounding=ROUND_HALF_UP,
    )
    return int(cents)


def convert_orders_to_usd_cents(apps, schema_editor):
    Cart = apps.get_model('orders', 'Cart')
    Order = apps.get_model('orders', 'Order')
    OrderItem = apps.get_model('orders', 'OrderItem')

    carts_to_update = []
    for cart in Cart.objects.all().iterator():
        cart.currency = 'USD'
        carts_to_update.append(cart)
        if len(carts_to_update) >= 500:
            Cart.objects.bulk_update(carts_to_update, ['currency'])
            carts_to_update.clear()
    if carts_to_update:
        Cart.objects.bulk_update(carts_to_update, ['currency'])

    orders_to_update = []
    for order in Order.objects.all().iterator():
        order.subtotal = _cop_to_usd_cents(order.subtotal)
        order.discount_total = _cop_to_usd_cents(order.discount_total)
        order.grand_total = _cop_to_usd_cents(order.grand_total)
        order.currency = 'USD'
        orders_to_update.append(order)
        if len(orders_to_update) >= 500:
            Order.objects.bulk_update(
                orders_to_update,
                ['subtotal', 'discount_total', 'grand_total', 'currency'],
            )
            orders_to_update.clear()
    if orders_to_update:
        Order.objects.bulk_update(
            orders_to_update,
            ['subtotal', 'discount_total', 'grand_total', 'currency'],
        )

    order_items_to_update = []
    for item in OrderItem.objects.all().iterator():
        item.unit_price = _cop_to_usd_cents(item.unit_price)
        item.line_total = _cop_to_usd_cents(item.line_total)
        order_items_to_update.append(item)
        if len(order_items_to_update) >= 500:
            OrderItem.objects.bulk_update(order_items_to_update, ['unit_price', 'line_total'])
            order_items_to_update.clear()
    if order_items_to_update:
        OrderItem.objects.bulk_update(order_items_to_update, ['unit_price', 'line_total'])


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_cart_uniqueness_constraints'),
    ]

    operations = [
        migrations.RunPython(convert_orders_to_usd_cents, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='cart',
            name='currency',
            field=models.CharField(default='USD', max_length=3),
        ),
        migrations.AlterField(
            model_name='order',
            name='currency',
            field=models.CharField(default='USD', max_length=3),
        ),
    ]
