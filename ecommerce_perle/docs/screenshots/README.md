# Screenshots

Este directorio contiene capturas de referencia del release actual.

## Storefront
- `home_desktop.png`
- `home_mobile360.png`
- `product_desktop.png`
- `product_mobile360.png`
- `cart_desktop.png`
- `cart_mobile360.png`
- `checkout_desktop.png`
- `checkout_mobile360.png`
- `confirmation_desktop.png`
- `confirmation_mobile360.png`

## Admin
- `admin-login.png`
- `admin-dashboard-premium.png`
- `admin-orders-changelist.png`
- `admin-orders-action-confirmation.png`
- `admin-stock-adjust-confirmation.png`

## Regeneración local (storefront)

Desde `ecommerce_perle/`:

```bash
source .venv/bin/activate
python manage.py runserver 127.0.0.1:8001
```

En otra terminal:

```bash
slug=$(curl -s http://127.0.0.1:8001/ | rg -o '/product/[^/]+/' | head -n1 | sed 's#^/product/##; s#/$##')

chromium --headless --disable-gpu --no-sandbox --window-size=1366,768 --screenshot=docs/screenshots/home_desktop.png http://127.0.0.1:8001/
chromium --headless --disable-gpu --no-sandbox --window-size=360,800 --screenshot=docs/screenshots/home_mobile360.png http://127.0.0.1:8001/

chromium --headless --disable-gpu --no-sandbox --window-size=1366,768 --screenshot=docs/screenshots/product_desktop.png "http://127.0.0.1:8001/product/${slug}/"
chromium --headless --disable-gpu --no-sandbox --window-size=360,800 --screenshot=docs/screenshots/product_mobile360.png "http://127.0.0.1:8001/product/${slug}/"

chromium --headless --disable-gpu --no-sandbox --window-size=1366,768 --screenshot=docs/screenshots/cart_desktop.png http://127.0.0.1:8001/cart/
chromium --headless --disable-gpu --no-sandbox --window-size=360,800 --screenshot=docs/screenshots/cart_mobile360.png http://127.0.0.1:8001/cart/

chromium --headless --disable-gpu --no-sandbox --window-size=1366,768 --screenshot=docs/screenshots/checkout_desktop.png http://127.0.0.1:8001/checkout/
chromium --headless --disable-gpu --no-sandbox --window-size=360,800 --screenshot=docs/screenshots/checkout_mobile360.png http://127.0.0.1:8001/checkout/
```

Para `confirmation_desktop.png` y `confirmation_mobile360.png`, se usa snapshot HTML local
con una orden de prueba ligada a sesión (evita fricción de autenticación/sesión en headless):

```bash
python manage.py shell -c "
from decimal import Decimal
from pathlib import Path
from django.test import Client
from django.test.utils import override_settings
from apps.catalog.models import Category, Product, ProductVariant
from apps.customers.models import Customer, Address
from apps.orders.models import Order, OrderItem

with override_settings(ALLOWED_HOSTS=['testserver']):
    c = Client()
    c.get('/')
    session_key = c.session.session_key

    category, _ = Category.objects.get_or_create(name='QA Screenshots', defaults={'slug': 'qa-screenshots'})
    product, _ = Product.objects.get_or_create(
        slug='qa-confirmation-product',
        defaults={'name': 'QA Confirmation Product', 'category': category, 'description': 'Producto de QA', 'is_active': True}
    )
    if product.category_id != category.id:
        product.category = category
        product.save(update_fields=['category'])

    variant, _ = ProductVariant.objects.get_or_create(
        sku='QA-CONF-001',
        defaults={'product': product, 'size': 'M', 'color': 'Aqua', 'price_cop': 129000, 'is_active': True}
    )
    if variant.product_id != product.id:
        variant.product = product
        variant.save(update_fields=['product'])

    customer, _ = Customer.objects.get_or_create(
        email='qa-confirmation@example.com',
        defaults={'full_name': 'QA Confirmation', 'phone': '50760000000'}
    )
    address, _ = Address.objects.get_or_create(
        customer=customer,
        line1='Costa del Este, Torre QA',
        city='Ciudad de Panamá',
        state='Panamá',
        country='PA',
        defaults={'postal_code': '0000'}
    )

    order = Order.objects.create(
        customer=customer,
        address=address,
        status='confirmed',
        subtotal=variant.price_cop,
        discount_total=0,
        grand_total=variant.price_cop,
        session_key=session_key,
    )
    OrderItem.objects.create(
        order=order,
        variant=variant,
        quantity=1,
        unit_price=variant.price_cop,
        line_total=variant.price_cop,
    )

    response = c.get(f'/orders/confirmation/{order.public_id}/')
    html = response.content.decode('utf-8')

css = Path('static/css/perle.css').read_text(encoding='utf-8')
html = html.replace('<link rel=\"stylesheet\" href=\"/static/css/perle.css\" />', f'<style>{css}</style>')
html = html.replace('<script src=\"/static/js/storefront.js\" defer></script>', '')
html = html.replace('/static/', '../../static/')
Path('docs/screenshots/confirmation-snapshot.html').write_text(html, encoding='utf-8')
"

chromium --headless --disable-gpu --no-sandbox --window-size=1366,768 --screenshot=docs/screenshots/confirmation_desktop.png "file://$(pwd)/docs/screenshots/confirmation-snapshot.html"
chromium --headless --disable-gpu --no-sandbox --window-size=360,800 --screenshot=docs/screenshots/confirmation_mobile360.png "file://$(pwd)/docs/screenshots/confirmation-snapshot.html"
rm -f docs/screenshots/confirmation-snapshot.html
```

`admin-dashboard-premium.png` requiere sesión autenticada de admin.
