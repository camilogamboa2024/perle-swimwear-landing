from django.db import transaction
from django.db.models import F

from apps.inventory.models import InventoryMovement, StockLevel
from apps.orders.models import Cart, Order, OrderItem, OrderStatusHistory
from apps.orders.services import calculate_cart_totals
from .whatsapp import build_whatsapp_message


class CheckoutError(ValueError):
    """Business-rule errors that should be exposed as controlled 4xx responses."""


@transaction.atomic
def create_order_from_cart(*, customer, address, cart, coupon=None, payment_method='whatsapp', session_key=''):
    locked_cart = Cart.objects.select_for_update().get(pk=cart.pk)
    items = list(
        locked_cart.items.select_related('variant', 'variant__product').order_by('variant_id', 'id')
    )
    if not items:
        raise CheckoutError('El carrito está vacío')

    variant_ids = [item.variant_id for item in items]
    locked_stocks = {
        stock.variant_id: stock
        for stock in (
            StockLevel.objects.select_for_update()
            .filter(variant_id__in=variant_ids)
            .order_by('variant_id')
        )
    }

    order = Order.objects.create(
        customer=customer,
        address=address,
        currency=locked_cart.currency,
        coupon=coupon,
        payment_method=payment_method,
        session_key=session_key or locked_cart.session_key,
    )

    for item in items:
        if not item.variant.is_active:
            raise CheckoutError(f'Variante no disponible para SKU {item.variant.sku}')
        stock = locked_stocks.get(item.variant_id)
        if stock is None:
            raise CheckoutError(f'Sin stock configurado para SKU {item.variant.sku}')
        if stock.available < item.quantity:
            raise CheckoutError(f'Sin stock para SKU {item.variant.sku}')

        stock.available = F('available') - item.quantity
        stock.save(update_fields=['available', 'updated_at'])
        InventoryMovement.objects.create(
            variant=item.variant,
            movement_type=InventoryMovement.OUT,
            quantity=-item.quantity,
            reason=f'Order #{order.id}',
        )
        line_total = item.quantity * item.variant.price_usd_cents
        OrderItem.objects.create(
            order=order,
            variant=item.variant,
            quantity=item.quantity,
            unit_price=item.variant.price_usd_cents,
            line_total=line_total,
        )

    totals = calculate_cart_totals(locked_cart, coupon)
    order.subtotal = totals['subtotal_cents']
    order.discount_total = totals['discount_total_cents']
    order.grand_total = totals['grand_total_cents']
    order.whatsapp_message = build_whatsapp_message(order)
    order.save(update_fields=['subtotal', 'discount_total', 'grand_total', 'whatsapp_message'])

    OrderStatusHistory.objects.create(order=order, from_status='', to_status=order.status)
    locked_cart.items.all().delete()
    return order
