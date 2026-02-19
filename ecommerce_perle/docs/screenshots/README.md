# Screenshots

Este directorio contiene capturas de referencia del release:
- `home.png`
- `product.png`
- `cart.png`
- `checkout.png`
- `confirmation.png`
- `admin-dashboard.png`

Si estás ejecutando localmente, puedes regenerarlas con:
```bash
source .venv/bin/activate
python manage.py runserver 127.0.0.1:8001
chromium --headless --disable-gpu --screenshot=docs/screenshots/home.png --window-size=1440,1024 http://127.0.0.1:8001/
```
