# Perle E-commerce Runtime

Aplicación Django + DRF para catálogo, carrito, checkout y operación interna con panel admin premium.

Este directorio es el runtime canónico del producto. La raíz del repo documenta qué se despliega y qué quedó archivado como legacy.
Mercado canónico actual: Panamá-first, con moneda USD y persistencia nueva en `country='Panama'`.

Branding activo: wordmark temporal limpio (`static/brand/perle-wordmark.png`) y favicon monograma (`static/brand/favicon.png`) en storefront + admin.
Cuando se reciba el logo oficial transparente final, se reemplaza este asset sin cambios de lógica.

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
- Precios y totales en USD (almacenados como centavos enteros para precisión).
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
- `SECURITY_PHASE` (`monitor` o `enforce`)
- `ADMIN_MFA_REQUIRED` (`0/1`, aplica a `staff/superusers`)
- `AXES_FAILURE_LIMIT`
- `AXES_COOLOFF_HOURS`

## Seguridad práctica por fases
- Fase monitor:
  - `SECURITY_PHASE=monitor`
  - `ADMIN_MFA_REQUIRED=0`
  - CSP en `Content-Security-Policy-Report-Only`
  - Lockout de admin con Axes (limite recomendado: `8`)
- Fase enforce:
  - `SECURITY_PHASE=enforce`
  - `ADMIN_MFA_REQUIRED=1`
  - CSP bloqueante (`Content-Security-Policy`)
  - Lockout mas estricto (limite recomendado: `5`)

MFA admin:
- Se habilita flujo TOTP en rutas ` /account/... ` (two-factor).
- Cuando `ADMIN_MFA_REQUIRED=1`, usuarios `staff/superuser` son redirigidos al flujo MFA antes de entrar a `/admin/`.
- El objetivo es hardening entendible para staging serio y producción pequeña/mediana, no claims enterprise.

### Nota CSRF
`storefront.js` usa cookie `csrftoken` para enviar `X-CSRFToken`, por eso `CSRF_COOKIE_HTTPONLY` permanece en `0` por defecto.  
Si cambias a `1`, debes migrar a estrategia con token en DOM/meta.

## Render (Blueprint)
En la raíz del repo existe `render.yaml` con `rootDir: ecommerce_perle`.
- `preDeployCommand`: ejecuta migraciones fuera del proceso web.
- `startCommand`: inicia solo Gunicorn.
- `healthCheckPath`: `/healthz/`.
- `autoDeployTrigger: checksPass`: evita auto deploys cuando la CI falla.

Estado de validación externa:
- El blueprint está verificado por código y checks locales.
- La validación externa sigue pendiente en GitHub/Render desde esta sesión.
- La última verificación pública del dominio documentado respondió `404 no-server`, así que no se declara staging ni producción desde este repo todavía.

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

Nota de dominio:
- El runtime nuevo persiste `country='Panama'`.
- Direcciones históricas creadas antes de esta corrección deben revisarse manualmente en admin si se sospecha que quedaron con país incorrecto por el default anterior.

## Smoke test post deploy (10 min)
0. `/healthz/` responde `200` con `{"status":"ok","service":"perle-ecommerce"}`.
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
coverage run manage.py test && coverage report
python manage.py collectstatic --noinput
ruff check .
bandit -q -r apps core -lll
pip-audit -r requirements.txt
semgrep --config p/django --config p/python apps core
```

Prueba dinamica local (servidor ya corriendo):
```bash
mkdir -p audit/security_round_local
python scripts/security/dast_auth_csrf.py --base-url http://127.0.0.1:8000 --out audit/security_round_local/dast_auth_csrf.json --failure-limit 8 --scope web
python scripts/security/verify_security_headers.py --base-url http://127.0.0.1:8000 --out audit/security_round_local/security_headers.json --phase monitor --scope web --dast-report audit/security_round_local/dast_auth_csrf.json
python scripts/security/gate_security.py --input-dir audit/security_round_local --out audit/security_round_local/security_gate_summary.json --markdown audit/security_round_local/security_gate_summary.md --strict-critical-high
```

Auditoria CVE:
- Fuente canónica: job CI (`quality-and-security`) que genera `pip-audit.json` como artifact.
- Coverage visible: el mismo job publica `coverage.txt` y `coverage.xml` como artifacts y resumen.
- En local sin internet, `pip-audit` puede fallar por entorno (DNS/salida).
- Opcional local corporativo: exportar `PIP_INDEX_URL` y/o `PIP_EXTRA_INDEX_URL` para usar mirror interno.
- `semgrep` usa `.semgrepignore` para excluir `.venv*`, `staticfiles/` y `audit/`.
- Los dos templates admin con falso positivo de parsing Django/CSRF quedan suprimidos con `nosemgrep` puntual, no por aceptación de riesgo.

## E2E local
```bash
npm install
npx playwright install chromium
npx playwright test --project=chromium
```

E2E QA aislado:
```bash
npm run test:e2e:qa
```

Estrés PostgreSQL local (dockerizado):
```bash
bash scripts/qa/run_pg_stress.sh
```

## QA manual
Checklist completa: `docs/QA_CHECKLIST.md`

## Runbook de operación
`docs/RUNBOOK.md`

## Criterio operativo honesto
- Apto para demo: sí.
- Listo para validación externa: sí.
- Staging serio: pendiente de verificación externa en GitHub/Render.
- Producción pequeña/mediana: no declarada.

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
