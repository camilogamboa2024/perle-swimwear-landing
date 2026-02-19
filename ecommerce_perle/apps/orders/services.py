def calculate_cart_totals(cart, coupon=None):
    subtotal = 0
    for item in cart.items.select_related('variant').all():
        subtotal += item.quantity * item.variant.price_cop
    coupon_is_valid = bool(coupon and coupon.is_valid_for_checkout())
    discount = int(subtotal * (coupon.percentage / 100)) if coupon_is_valid else 0
    return {
        'subtotal': subtotal,
        'discount_total': discount,
        'grand_total': max(subtotal - discount, 0),
    }
