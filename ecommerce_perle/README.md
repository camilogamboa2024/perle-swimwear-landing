# Perle E-commerce MVP (Django)

Implementación de e-commerce boutique para Perle Swimwear, enfocada en flujo de compra rápido, control de inventario y checkout asistido por WhatsApp.

## 1. Resumen ejecutivo
Este repositorio contiene una aplicación Django + DRF con:

- Catálogo público y detalle de productos con variantes activas.
- Carrito por sesión (anónimo) o por usuario autenticado.
- Checkout transaccional con bloqueo de stock (`select_for_update`).
- Confirmación de pedido protegida por `public_id` + `session_key`.
- Integración de salida a WhatsApp (`wa.me`) para cierre de venta.
- Endpoints mutables protegidos por validación CSRF de sesión.

## 2. Stack técnico
- Backend: Django 5, Django REST Framework.
- Frontend: Django Templates + JavaScript vanilla (`static/js/storefront.js`).
- DB local: SQLite.
- Producción recomendada: PostgreSQL (vía `DATABASE_URL`).
- Servidor: Gunicorn + WhiteNoise (estáticos).

Dependencias principales en `requirements.txt`:
- `Django`
- `djangorestframework`
- `gunicorn`
- `whitenoise`
- `psycopg[binary]`
- `dj-database-url`

## 3. Arquitectura por módulos
- `apps/catalog`: categorías, productos, variantes, imágenes y APIs de catálogo.
- `apps/inventory`: stock actual (`StockLevel`) y movimientos (`InventoryMovement`).
- `apps/orders`: carrito, órdenes, historial de estado y APIs de carrito.
- `apps/checkout`: confirmación de checkout y construcción de mensajes WhatsApp.
- `apps/customers`: clientes y direcciones.
- `core`: configuración global, URLs, context processors y autenticación CSRF reforzada.

## 4. Flujos críticos implementados
1. Visualizar catálogo (`/`, `/product/<slug>/`).
2. Añadir/editar/eliminar ítems de carrito vía API.
3. Confirmar checkout vía `POST /checkout/api/checkout/confirm/`.
4. Descontar inventario y registrar movimientos en transacción atómica.
5. Consultar confirmación de pedido por `public_id` solo con sesión autorizada.
6. Abrir finalización por WhatsApp cuando `WHATSAPP_PHONE` está configurado.

## 5. Modelo de datos (resumen)
- Catálogo:
  - `Category -> Product -> ProductVariant -> StockLevel`
  - `Product -> ProductImage`
- Órdenes:
  - `Cart -> CartItem`
  - `Order -> OrderItem`
  - `Order -> OrderStatusHistory`
  - `Order` referencia `Customer`, `Address` y opcional `Coupon`.
- Inventario:
  - `StockLevel` (cantidad disponible actual)
  - `InventoryMovement` (histórico de entradas/salidas/ajustes)

## 6. Endpoints principales
Vistas web:
- `GET /`
- `GET /product/<slug>/`
- `GET /cart/`
- `GET /checkout/`
- `GET /orders/confirmation/<uuid:public_id>/`
- `GET /legal/terms/`
- `GET /legal/privacy/`
- `GET /legal/shipping-returns/`

APIs:
- `GET /api/products/`
- `GET /api/products/<slug>/`
- `GET /api/cart/`
- `POST /api/cart/items/`
- `PATCH /api/cart/items/<item_id>/`
- `DELETE /api/cart/items/<item_id>/`
- `POST /api/cart/clear/`
- `POST /checkout/api/checkout/confirm/`

Ejemplo de `POST /checkout/api/checkout/confirm/`:

```json
{
  "full_name": "Cliente Demo",
  "email": "cliente@example.com",
  "phone": "3001234567",
  "line1": "Calle 123",
  "city": "Bogota",
  "state": "DC",
  "coupon_code": "",
  "payment_method": "whatsapp"
}
```

Respuesta exitosa (201):

```json
{
  "order_id": 10,
  "order_public_id": "uuid",
  "whatsapp_url": "https://wa.me/...",
  "confirmation_url": "/orders/confirmation/uuid/"
}
```

## 7. Seguridad implementada
- CSRF reforzado en endpoints mutables por sesión:
  - `POST /api/cart/items/`
  - `PATCH/DELETE /api/cart/items/<item_id>/`
  - `POST /api/cart/clear/`
  - `POST /checkout/api/checkout/confirm/`
- Checkout en transacción atómica:
  - crea orden + descuenta stock + crea movimientos + limpia carrito.
- Validaciones de negocio:
  - carrito no vacío
  - variante activa
  - stock configurado y suficiente
  - rollback de datos de cliente/dirección ante error de checkout.
- Confirmación de pedido protegida por sesión:
  - si la sesión no coincide con la de la orden, responde 404.
- Frontend de checkout:
  - renderizado seguro de errores/links (sin inyección HTML directa).
- Rate limit DRF:
  - checkout: `20/hour`.

## 8. Instalación paso a paso (Linux y Windows)

### 8.1 Prerrequisitos
- Python `3.11+` instalado.
- `pip` disponible.
- Git instalado.
- Terminal:
  - Linux/macOS: Bash/Zsh.
  - Windows: PowerShell o CMD.

Verifica versión de Python:

```bash
python --version
```

Si tu sistema usa `python3`, reemplaza `python` por `python3` en todos los comandos.

### 8.2 Linux/macOS (Bash/Zsh)
1. Clonar y entrar al proyecto:

```bash
git clone <URL_DEL_REPO>
cd ecommerce_perle
```

2. Crear y activar entorno virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Crear archivo de entorno:

```bash
cp .env.example .env
```

5. Ejecutar migraciones:

```bash
python manage.py migrate --noinput
```

6. Cargar datos demo:

```bash
python manage.py seed_demo
```

7. Crear superusuario (opcional pero recomendado):

```bash
python manage.py createsuperuser
```

8. Levantar servidor:

```bash
python manage.py runserver
```

9. Abrir en navegador:
- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/admin/`

### 8.3 Windows (PowerShell)
1. Clonar y entrar al proyecto:

```powershell
git clone <URL_DEL_REPO>
cd ecommerce_perle
```

2. Crear entorno virtual:

```powershell
py -m venv .venv
```

3. Activar entorno virtual:

```powershell
.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea scripts, habilita ejecución para tu usuario y vuelve a activar:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\Activate.ps1
```

4. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

5. Crear archivo de entorno:

```powershell
Copy-Item .env.example .env
```

6. Ejecutar migraciones y seed:

```powershell
python manage.py migrate --noinput
python manage.py seed_demo
```

7. Crear superusuario (opcional):

```powershell
python manage.py createsuperuser
```

8. Levantar servidor:

```powershell
python manage.py runserver
```

### 8.4 Windows (CMD)
1. Clonar y entrar al proyecto:

```bat
git clone <URL_DEL_REPO>
cd ecommerce_perle
```

2. Crear entorno virtual:

```bat
py -m venv .venv
```

3. Activar entorno virtual:

```bat
.venv\Scripts\activate.bat
```

4. Instalar dependencias:

```bat
pip install -r requirements.txt
```

5. Crear archivo de entorno:

```bat
copy .env.example .env
```

6. Ejecutar migraciones y seed:

```bat
python manage.py migrate --noinput
python manage.py seed_demo
```

7. Crear superusuario (opcional):

```bat
python manage.py createsuperuser
```

8. Levantar servidor:

```bat
python manage.py runserver
```

### 8.5 Verificación rápida post-instalación
Con el servidor arriba, valida:
- `GET /` home
- `GET /cart/`
- `GET /checkout/`
- `GET /legal/terms/`

Comandos recomendados:

```bash
python manage.py check
python manage.py test
```

## 9. Variables de entorno
Base (`.env.example`):
- `DJANGO_SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `DB_ENGINE`, `DB_NAME`, `DB_CONN_MAX_AGE`, `DB_SSL_REQUIRE`
- `WHATSAPP_PHONE`
- `CURRENCY_USD_RATE`

Hardening recomendado en producción:
- `DEBUG=0`
- `SECURE_SSL_REDIRECT=1`
- `SECURE_HSTS_SECONDS` (ej. `300` inicial, luego mayor)
- `SECURE_HSTS_INCLUDE_SUBDOMAINS=1`
- `SECURE_HSTS_PRELOAD` según política de dominio
- `SESSION_COOKIE_SAMESITE=Lax`
- `CSRF_COOKIE_SAMESITE=Lax`

Nota:
- Si `DATABASE_URL` está vacío, usa fallback de engine local.
- En `DEBUG=0`, el proyecto bloquea SQLite por seguridad de despliegue.

## 10. Comandos de calidad recomendados
```bash
python manage.py check
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --noinput
python -m compileall .
```

## 11. Deploy en Render
Recomendaciones:
- `render.yaml` en raíz del repo (con `rootDir: ecommerce_perle`).
- Build:
  - `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`
- Start:
  - `gunicorn core.wsgi:application`

Importante:
- Ejecutar `python manage.py seed_demo` solo una vez en producción.
- No hardcodear `WHATSAPP_PHONE` en código; definirlo como variable de entorno.

## 12. Smoke test post-deploy (10 min)
1. `/` carga con estilos y productos.
2. Añadir al carrito actualiza badge y total.
3. `/cart/` muestra ítems y totales correctos.
4. `/checkout/` crea orden y devuelve links.
5. `/orders/confirmation/<uuid>/` funciona con la misma sesión y bloquea otras.
6. Legales (`/legal/*`) responden 200.
7. Con `WHATSAPP_PHONE` vacío: sin links/FAB WhatsApp.

## 13. Estado actual y limitaciones conocidas
- `wompi/stripe` están declarados como opciones, pero no hay integración de cobro real todavía (gateway actual es dummy).
- El flujo principal está orientado a checkout por WhatsApp.
- La app no implementa upload de archivos de usuario.

## 14. Auditoría y trazabilidad
Se dejó carpeta `audit/` con evidencia técnica de revisión AppSec + QA:
- baseline de entorno
- smoke
- pruebas dinámicas manuales
- regresión post-fix
- reporte final y checklist de release

Archivos clave:
- `audit/final_report.md`
- `audit/release_checklist.md`
- `audit/commands.log`

---
Si quieres convertir este MVP en versión productiva “ready-to-scale”, el siguiente paso recomendado es integrar pasarela real de pagos, observabilidad centralizada y pipeline CI con SAST/CVE/coverage automáticos.
