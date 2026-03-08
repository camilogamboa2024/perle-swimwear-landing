def calculate_cart_totals(cart, coupon=None):
    subtotal = 0
    for item in cart.items.select_related('variant').all():
        subtotal += item.quantity * item.variant.price_usd_cents
    coupon_is_valid = bool(coupon and coupon.is_valid_for_checkout())
    discount = int(subtotal * (coupon.percentage / 100)) if coupon_is_valid else 0
    grand_total = max(subtotal - discount, 0)
    return {
        'subtotal_cents': subtotal,
        'discount_total_cents': discount,
        'grand_total_cents': grand_total,
        # Legacy aliases kept during transition window.
        'subtotal': subtotal,
        'discount_total': discount,
        'grand_total': grand_total,
    }
