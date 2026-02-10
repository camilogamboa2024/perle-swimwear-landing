# Perle E-commerce MVP (Django)

## Qué incluye
- Catálogo público + detalle de producto con variantes y stock.
- API DRF para productos, carrito y confirmación de checkout.
- Checkout transaccional con control de inventario (`select_for_update`) y fallback WhatsApp.
- Confirmación protegida por `public_id` (UUID) y validación de `session_key`.
- Header/footer premium, badge de carrito y botón flotante de WhatsApp.

## Setup local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate --noinput
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

## Variables de entorno (local/Render)
- `DJANGO_SECRET_KEY`
- `DEBUG` (`0` en producción)
- `ALLOWED_HOSTS` (ej: `perle-ecommerce.onrender.com`)
- `CSRF_TRUSTED_ORIGINS` (ej: `https://perle-ecommerce.onrender.com`)
- `DATABASE_URL` (Postgres de Render, obligatorio en producción)
- `DB_CONN_MAX_AGE` (ej: `600`)
- `DB_SSL_REQUIRE` (`1` en Render)
- `WHATSAPP_PHONE` (opcional)
- `CURRENCY_USD_RATE`
- `SECURE_SSL_REDIRECT` (recomendado `1`)
- `SECURE_HSTS_SECONDS` (arranque recomendado `300`, luego subir)

> Si `DATABASE_URL` no está definido, Django usa fallback `DB_ENGINE/DB_NAME/...`. En `DEBUG=0`, SQLite queda bloqueado por configuración para evitar deploy accidental sin Postgres.

## Deploy en Render
- No ejecutes `seed_demo` en cada deploy de producción.
- Ejecuta `python manage.py seed_demo` **una sola vez** (local o Render Shell) para poblar catálogo demo.
- `render.yaml` está en la **raíz del repo** y define `rootDir: ecommerce_perle`.
- Build command:
  - `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`
- Start command:
  - `gunicorn core.wsgi:application`


### Variables env mínimas (Render)
- `DJANGO_SECRET_KEY`
- `DEBUG=0`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `WHATSAPP_PHONE` (opcional)

## Verificaciones recomendadas
```bash
python manage.py check
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --noinput
python -m compileall ecommerce_perle
```

> Nota: en entornos sin Django instalado (ej. sandbox con proxy restringido), `manage.py check/test/migrate` no podrán ejecutarse hasta instalar dependencias. En Render sí corren durante el build.

## URLs clave para validar
- `/`
- `/cart/`
- `/checkout/`
- `/orders/confirmation/<uuid>/`
- `/legal/terms/`
- `/legal/privacy/`
- `/legal/shipping-returns/`

## Checklist manual (local/Render)
1. Ejecutar `python manage.py seed_demo` y confirmar catálogo visible en `/`.
2. Agregar al carrito desde home/detalle actualiza badge y total.
3. `/cart/` muestra items y totales.
4. `/checkout/` confirma orden y redirige a `/orders/confirmation/<uuid>/`.
5. Si `WHATSAPP_PHONE` está configurado, botón WhatsApp abre `wa.me/<WHATSAPP_PHONE>`.
6. Páginas legales cargan sin 404.


## Smoke test post-deploy (10 min)
1. `/` carga con estilos y catálogo visible.
2. Agregar al carrito actualiza badge y no rompe total mini.
3. `/cart/` muestra items + totales.
4. `/checkout/` muestra estado `Procesando...`, crea orden y devuelve links.
5. `/orders/confirmation/<uuid>/` carga con misma sesión y bloquea accesos sin session_key.
6. `/legal/terms/`, `/legal/privacy/`, `/legal/shipping-returns/` sin 404.
7. Con `WHATSAPP_PHONE` vacío: no se renderizan link/FAB WhatsApp y no hay errores UI.


## Post-merge checklist (rápido)
1. Confirmar variables mínimas en Render (`DJANGO_SECRET_KEY`, `DEBUG=0`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`).
2. Deploy exitoso con estáticos cargando (CSS/JS presentes).
3. En Render Shell: `python manage.py seed_demo` una sola vez en prod (`--reset` solo staging/qa).
4. Probar `/cart/`, `/checkout/`, `/orders/confirmation/<uuid>/`.
5. Probar escenario con `WHATSAPP_PHONE` vacío: sin link/FAB y sin errores UI.


## Render Shell (validación final)
Después del primer deploy, ejecutar:

```bash
python manage.py check --deploy
python manage.py test
python manage.py seed_demo  # una vez en prod
```

Si es staging/QA:

```bash
python manage.py seed_demo --reset
```


## CSRF y frontend
- `storefront.js` lee `csrftoken` desde cookie para enviar `X-CSRFToken` en fetch.
- Por eso `CSRF_COOKIE_HTTPONLY` queda configurable y por defecto desactivado (`0`).
- Si lo activas (`1`), debes pasar token CSRF vía template/meta y ajustar JS.


## Render Blueprint y `WHATSAPP_PHONE`
- En `render.yaml`, `WHATSAPP_PHONE` está como `sync: false` para evitar hardcodear números.
- En Create-from-Blueprint, Render no inyecta valor por defecto para ese env var.
- Resultado: si no defines `WHATSAPP_PHONE`, la UI oculta links/FAB de WhatsApp (comportamiento esperado).

Codex review test
