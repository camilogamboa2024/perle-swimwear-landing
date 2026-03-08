from urllib.parse import quote_plus

from apps.orders.money import format_usd


def build_whatsapp_message(order):
    lines = [
        'Hola Perle Swimwear ✨',
        f'Quiero confirmar mi pedido #{order.id}',
        '',
        'Items:'
    ]
    for item in order.items.select_related('variant__product').all():
        lines.append(
            f"- {item.variant.product.name} | Talla {item.variant.size} | Color {item.variant.color} | x{item.quantity} | {format_usd(item.line_total)}"
        )
    lines += [
        '',
        f'Subtotal: {format_usd(order.subtotal)}',
        f'Descuento: {format_usd(order.discount_total)}',
        f'Total: {format_usd(order.grand_total)}',
        '',
        f'Entrega: {order.address.line1}, {order.address.city}, {order.address.state}',
        f'Contacto: {order.customer.phone or order.customer.email}',
        '',
        'Gracias 💖',
    ]
    return '\n'.join(lines)


def build_whatsapp_url(message, phone_number):
    return f'https://wa.me/{phone_number}?text={quote_plus(message)}'
