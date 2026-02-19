# Screenshots

Este directorio contiene capturas de referencia del release:
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
- `admin-login.png`
- `admin-dashboard-premium.png`
- `admin-orders-changelist.png`
- `admin-orders-action-confirmation.png`
- `admin-stock-adjust-confirmation.png`

Si estás ejecutando localmente, puedes regenerarlas con:
```bash
source .venv/bin/activate
python manage.py runserver 127.0.0.1:8001
chromium --headless --disable-gpu --screenshot=docs/screenshots/home_desktop.png --window-size=1440,1024 http://127.0.0.1:8001/
chromium --headless --disable-gpu --screenshot=docs/screenshots/home_mobile360.png --window-size=360,800 http://127.0.0.1:8001/
chromium --headless --disable-gpu --screenshot=docs/screenshots/admin-login.png --window-size=1440,1024 http://127.0.0.1:8001/admin/login/
chromium --headless --disable-gpu --screenshot=docs/screenshots/admin-dashboard-premium.png --window-size=1440,1024 http://127.0.0.1:8001/admin/
```
