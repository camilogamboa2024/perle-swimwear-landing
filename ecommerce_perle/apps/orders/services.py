def calculate_cart_totals(cart, coupon=None):
    subtotal = 0
    for item in cart.items.select_related('variant').all():
        subtotal += item.quantity * item.variant.price_cop
    discount = int(subtotal * (coupon.percentage / 100)) if coupon and coupon.is_active else 0
    return {
        'subtotal': subtotal,
        'discount_total': discount,
        'grand_total': max(subtotal - discount, 0),
    }
