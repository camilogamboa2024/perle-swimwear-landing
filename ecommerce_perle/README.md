# Perle E-commerce (Production-Ready + Premium UI)

Aplicación Django + DRF para catálogo, carrito, checkout y operación interna con panel admin premium.

Branding activo: logo oficial del negocio (`static/brand/perle-logo.png`) y favicon (`static/brand/favicon.png`) en storefront + admin.

## Stack
- Django 5.x + DRF
- Templates + CSS/JS vanilla (`static/css/perle.css`, `static/js/storefront.js`)
- Tipografía storefront: `Manrope` (Google Fonts) + fallback system
- WhiteNoise + Gunicorn
- SQLite (local) / PostgreSQL (`DATABASE_URL`) en producción
- Theme admin: Jazzmin
- E2E: Playwright (Chromium CI)

## Funcionalidades principales
- Catálogo y detalle de producto con variantes activas.
- Carrito API/SSR (add, update, delete, clear).
- Checkout transaccional con lock de stock.
- Confirmación protegida por `public_id + session_key`.
- WhatsApp opcional:
  - Si `WHATSAPP_PHONE` está vacío: no se renderiza `wa.me` ni FAB.
  - Si tiene valor: se renderizan enlaces seguros.
- Admin operativo:
  - Órdenes con acciones masivas (`paid`, `shipped`, `delivered`, `cancelled`) y confirmación.
  - Inventario con ajuste masivo y registro en `InventoryMovement`.
  - Cupones con activación/desactivación + expiración.
  - Dashboard admin premium con KPIs, tendencias y módulos accionables.
  - Interfaz admin en español con estilo luxury dark-slate.

## Setup local
```bash
cd ecommerce_perle
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
python manage.py migrate --noinput
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Rutas:
- Storefront: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Variables de entorno mínimas
Archivo base: `.env.example`

Variables clave:
- `DJANGO_SECRET_KEY` (en prod usar valor largo y aleatorio)
- `DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `WHATSAPP_PHONE` (opcional)
- `LOW_STOCK_THRESHOLD`
- `CURRENCY_USD_RATE`

### Nota CSRF
`storefront.js` usa cookie `csrftoken` para enviar `X-CSRFToken`, por eso `CSRF_COOKIE_HTTPONLY` permanece en `0` por defecto.  
Si cambias a `1`, debes migrar a estrategia con token en DOM/meta.

## Render (Blueprint)
En la raíz del repo existe `render.yaml` con `rootDir: ecommerce_perle`.

Variables recomendadas en Render:
- `DJANGO_SECRET_KEY` (generateValue)
- `DEBUG=0`
- `ALLOWED_HOSTS=<tu-dominio-render>`
- `CSRF_TRUSTED_ORIGINS=https://<tu-dominio-render>`
- `DATABASE_URL` (desde la DB de Render)
- `DB_CONN_MAX_AGE=600`
- `DB_SSL_REQUIRE=1`
- `WHATSAPP_PHONE` (opcional)
- `SECURE_HSTS_PRELOAD=1`

## Smoke test post deploy (10 min)
1. `/` carga estilos y cards premium.
2. Agregar producto al carrito actualiza badge y total.
3. `/cart/` permite subir/bajar cantidad, eliminar y vaciar.
4. `/checkout/` confirma orden y muestra confirmación.
5. `/orders/confirmation/<uuid>/`:
   - misma sesión: `200`
   - sesión diferente: `404`
6. Con `WHATSAPP_PHONE=""`: no debe existir `wa.me`.
7. Con `WHATSAPP_PHONE` con valor: aparecen links WA en footer/FAB/confirmación.
8. Admin:
   - KPIs visibles en home de admin.
   - acciones masivas de órdenes funcionan.
   - ajuste de inventario registra movimientos.

## Calidad, seguridad y tests
```bash
python manage.py check
DEBUG=0 DJANGO_SECRET_KEY='long-secret-50-plus-characters' ALLOWED_HOSTS='perle-ecommerce.onrender.com' CSRF_TRUSTED_ORIGINS='https://perle-ecommerce.onrender.com' DATABASE_URL='sqlite:///db.sqlite3' python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --noinput
ruff check .
bandit -q -r apps core -lll
pip-audit -r requirements.txt
```

## E2E local
```bash
npm install
npx playwright install chromium
npx playwright test --project=chromium
```

## QA manual
Checklist completa: `docs/QA_CHECKLIST.md`

## Runbook de operación
`docs/RUNBOOK.md`

## Screenshots
- `docs/screenshots/home_desktop.png`
- `docs/screenshots/home_mobile360.png`
- `docs/screenshots/product_desktop.png`
- `docs/screenshots/product_mobile360.png`
- `docs/screenshots/cart_desktop.png`
- `docs/screenshots/cart_mobile360.png`
- `docs/screenshots/checkout_desktop.png`
- `docs/screenshots/checkout_mobile360.png`
- `docs/screenshots/confirmation_desktop.png`
- `docs/screenshots/confirmation_mobile360.png`
- `docs/screenshots/admin-login.png`
- `docs/screenshots/admin-dashboard-premium.png`
- `docs/screenshots/admin-orders-changelist.png`
- `docs/screenshots/admin-orders-action-confirmation.png`
- `docs/screenshots/admin-stock-adjust-confirmation.png`
