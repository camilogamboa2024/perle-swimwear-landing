# System Map — QA Functional Round

## Contexto
- Repo: `/home/kicksdoors/Desktop/perle-swimwear-landing/ecommerce_perle`
- Stack: Django 5 + DRF + templates Django + JS vanilla + SQLite local
- Entorno: local
- Roles evaluados:
1. Anónimo (sesión)
2. Usuario autenticado
3. Admin Django

## Módulos / apps
- `apps/catalog`: catálogo público, detalle, API de productos.
- `apps/orders`: carrito por sesión/usuario, confirmación de orden por `public_id`.
- `apps/checkout`: confirmación de checkout, integración de mensaje/URL WhatsApp.
- `apps/inventory`: niveles de stock y movimientos.
- `apps/customers`: customer + address.
- `core`: settings, urls, auth helper CSRF.

## Rutas principales
### Web
- `GET /`
- `GET /product/<slug>/`
- `GET /cart/`
- `GET /checkout/`
- `GET /orders/confirmation/<uuid>/`
- `GET /admin/login/`
- `GET /legal/terms/`
- `GET /legal/privacy/`
- `GET /legal/shipping-returns/`

### API
- `GET /api/products/`
- `GET /api/products/<slug>/`
- `GET /api/cart/`
- `POST /api/cart/items/`
- `PATCH /api/cart/items/<item_id>/`
- `DELETE /api/cart/items/<item_id>/`
- `POST /api/cart/clear/`
- `POST /checkout/api/checkout/confirm/`

## Entidades principales
- `Category`, `Product`, `ProductVariant`, `ProductImage`
- `StockLevel`, `InventoryMovement`
- `Customer`, `Address`
- `Cart`, `CartItem`, `Coupon`, `Order`, `OrderItem`, `OrderStatusHistory`

## Matriz rol vs acción (validada)
| Acción | Anónimo | Auth user | Admin |
|---|---|---|---|
| Ver catálogo y detalle | Sí | Sí | Sí |
| Crear/editar/eliminar carrito | Sí (sesión + CSRF) | Sí (customer + CSRF) | Sí |
| Confirmar checkout | Sí (sesión + CSRF) | Sí (customer + CSRF) | Sí |
| Ver confirmación de orden | Solo sesión dueña | Solo sesión dueña | Sí (por admin, vía panel) |
| Acceder panel admin | No | No | Sí |

## Integraciones funcionales
- WhatsApp URL (`wa.me`) para continuidad de compra.
- Pagos `wompi/stripe`: declarados en choices, no integración E2E activa en este repo.
