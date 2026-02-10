# Revisión Manual AppSec (módulo por módulo)

## 4.1 Autenticación
- `apps/orders/views.py`: carrito por sesión anónima o `request.user` autenticado.
- `core/settings.py`: cookies `HttpOnly`, `SameSite`, y `Secure` condicionadas por `DEBUG=0`.
- Resultado: sin bypass directo de login/admin en pruebas manuales (`/admin/` redirige a login para anónimos).

## 4.2 Autorización / IDOR
- `apps/orders/views.py` filtra `CartItem` por `cart=cart_actual`.
- `apps/orders/views.py` validación de `session_key` en confirmación de orden.
- DAST: cambio de sesión en `orders/confirmation/<uuid>` da `404`.
- DAST: intento de patch/delete de `item_id` ajeno da `404`.

## 4.3 Validación de inputs
- Serializers DRF activos (`apps/checkout/serializers.py`, `apps/orders/serializers.py`).
- Límites básicos de longitud y tipos presentes.
- Se reforzó validación de stock para cart add/update en backend.

## 4.4 Inyecciones
- No se detectó SQL concatenado manual; ORM de Django en uso.
- No se detectó command injection (`subprocess/os.system/eval/exec`) en app code.

## 4.5 XSS
- Frontend de checkout usa `textContent` para errores y render seguro de links.
- DAST de query `q=<script>alert(1)</script>` no reflejó payload ejecutable.

## 4.6 CSRF + CORS
- Hallazgo HIGH confirmado y cerrado: APIs mutables aceptaban POST/PATCH/DELETE sin token CSRF.
- Fix aplicado: `core/authentication.py` + `authentication_classes` en vistas mutables.
- Re-test: sin token => `403`; con token => éxito.
- CORS: no middleware de CORS abierto detectado (same-origin por defecto).

## 4.7 SSRF
- No hay endpoints server-side que reciban URL arbitraria y hagan fetch HTTP saliente.

## 4.8 Archivos
- No hay upload/download de archivos de usuario.

## 4.9 Errores, logs y privacidad
- En local (`DEBUG=1`) hay mensajes de error de desarrollo.
- En flujo de checkout, errores de negocio devuelven `400` controlado (no `500`).

## 4.10 Configuración de producción
- Con `DEBUG=0`, settings activan `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`.
- `SECURE_HSTS_PRELOAD` queda en `0` por defecto (warning `security.W021`).

## 4.11 Resultado
- CRITICAL abiertos: 0
- HIGH abiertos: 0
- MEDIUM/LOW abiertos: ver `audit/final_report.md`
