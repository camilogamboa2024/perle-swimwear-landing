from django.db import transaction
from django.db.models import F

from apps.inventory.models import InventoryMovement, StockLevel
from apps.orders.models import Order, OrderItem, OrderStatusHistory
from apps.orders.services import calculate_cart_totals
from .whatsapp import build_whatsapp_message


@transaction.atomic
def create_order_from_cart(*, customer, address, cart, coupon=None, payment_method='whatsapp', session_key=''):
    items = list(cart.items.select_related('variant', 'variant__product'))
    if not items:
        raise ValueError('El carrito está vacío')

    order = Order.objects.create(
        customer=customer,
        address=address,
        currency=cart.currency,
        coupon=coupon,
        payment_method=payment_method,
        session_key=session_key or cart.session_key,
    )

    for item in items:
        stock = StockLevel.objects.select_for_update().get(variant=item.variant)
        if stock.available < item.quantity:
            raise ValueError(f'Sin stock para SKU {item.variant.sku}')

        stock.available = F('available') - item.quantity
        stock.save(update_fields=['available', 'updated_at'])
        InventoryMovement.objects.create(
            variant=item.variant,
            movement_type=InventoryMovement.OUT,
            quantity=-item.quantity,
            reason=f'Order #{order.id}',
        )
        line_total = item.quantity * item.variant.price_cop
        OrderItem.objects.create(
            order=order,
            variant=item.variant,
            quantity=item.quantity,
            unit_price=item.variant.price_cop,
            line_total=line_total,
        )

    totals = calculate_cart_totals(cart, coupon)
    order.subtotal = totals['subtotal']
    order.discount_total = totals['discount_total']
    order.grand_total = totals['grand_total']
    order.whatsapp_message = build_whatsapp_message(order)
    order.save(update_fields=['subtotal', 'discount_total', 'grand_total', 'whatsapp_message'])

    OrderStatusHistory.objects.create(order=order, from_status='', to_status=order.status)
    cart.items.all().delete()
    return order
