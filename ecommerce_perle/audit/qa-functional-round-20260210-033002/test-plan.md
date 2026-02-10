# Test Plan — QA Funcional

## Flujos críticos cubiertos
1. Catálogo y detalle de producto.
2. Mutaciones de carrito (add/patch/delete/clear).
3. Checkout confirm.
4. Confirmación de orden por `public_id + session_key`.
5. Login admin (válido e inválido).
6. WhatsApp on/off.

## Casos maestros
| Caso ID | Flujo | Objetivo | Precondiciones | Datos | Pasos | Resultado esperado | Evidencia |
|---|---|---|---|---|---|---|---|
| QA-CT-001 | Catálogo | Home carga correctamente | DB con seed | N/A | `GET /` | 200 y HTML renderizado | `test-results/smoke_client.log` |
| QA-CT-002 | Catálogo | API lista productos | Seed cargado | N/A | `GET /api/products/` | 200, lista JSON | `test-results/smoke_client.log` |
| QA-CT-003 | Carrito | Requiere CSRF en mutaciones | Cliente sin header CSRF | variant_id válido | `POST /api/cart/items/` sin token | 403 controlado | `test-results/smoke_client.log`, `apps/orders/tests.py` |
| QA-CT-004 | Carrito | Stock límite en add | Variant con stock=2 | quantity=3 | `POST /api/cart/items/` | 400 y sin item persistido | `apps/orders/tests.py`, `test-results/manage_test_post_fix.log` |
| QA-CT-005 | Carrito | Stock límite en patch | Item quantity=1 | patch quantity=3 | `PATCH /api/cart/items/<id>/` | 400 y quantity se mantiene | `apps/orders/tests.py` |
| QA-CT-006 | Checkout | Carrito vacío responde 4xx | Sesión sin items | payload válido | `POST /checkout/api/checkout/confirm/` | 400 JSON controlado | `test-results/smoke_client.log` |
| QA-CT-007 | Checkout | Flujo feliz end-to-end | Item en carrito con stock | payload válido | add item -> confirm | 201 + URL confirmación | `test-results/smoke_client.log` |
| QA-CT-008 | Checkout | Sin stock responde controlado | Item en carrito, stock bajado a 0 | payload válido | confirm checkout | 400 JSON, sin 500 | `test-results/smoke_client.log` |
| QA-CT-009 | Orden | Confirmación protegida por sesión | Orden creada | misma/diferente sesión | `GET confirmation_url` | 200 misma sesión, 404 otra | `test-results/smoke_client.log` |
| QA-CT-010 | Admin | Login inválido/válido | Superuser de prueba | credenciales inválidas/válidas | `POST /admin/login/` | inválido 200 (sin acceso), válido 302 `/admin/` | `test-results/admin_login_smoke.log` |
| QA-CT-011 | Bug hunt | Inputs inválidos no rompen app | CSRF válido | email inválido, qty<=0, IDs inexistentes | requests de fuzz funcional | 400/404 esperados, sin 500 | `test-results/bug_hunt_client.log` |
| QA-CT-012 | Reintento | Doble submit checkout | Item único en carrito | mismo payload x2 | confirm x2 | 201 primera, 400 segunda | `apps/checkout/tests.py`, `test-results/bug_hunt_client.log` |

## Criterio de aceptación aplicado
- BLOCKER abiertos: 0
- CRITICAL abiertos: 0
- HIGH abiertos: 0
