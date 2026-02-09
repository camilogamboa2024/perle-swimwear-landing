# Perle Swimwear — Diagnóstico y plan de migración a e-commerce Django

## OUTPUT 1 — Diagnóstico

> **Limitación**: no fue posible clonar el repo CRM por restricción de red (HTTP 403). Se documenta diagnóstico con `SUPUESTO` basado en patrones típicos CRM Django rentadora.

### A) Qué reutilizar del CRM (patrones)
- **Transacciones con lock pesimista** para recursos escasos (adaptar de reservas a stock por variante).
- **Mixins de permisos staff/manager** para panel interno y vistas de métricas.
- **Exportes CSV/PDF y plantillas de email** como base para factura/confirmación de orden.
- **Dashboard operativo** (KPIs de actividad diaria/mensual, alarmas de pendientes).

### B) Qué no sirve o debe reescribirse
- Reglas de calendario y overlap de reservas (no aplican literal al carrito).
- Dominio de contratos/alquiler y estados ligados a devolución.
- Front actual con catálogo hardcodeado en JavaScript (migrar a backend dinámico).

### C) Riesgos principales
- **Inventario**: race conditions en checkout simultáneo.
- **Pagos**: acoplarse pronto a proveedor concreto.
- **Performance**: filtros de catálogo sin índices + imágenes pesadas.
- **Seguridad**: exposición de PII en logs, ausencia de throttling.

### D) Arquitectura final propuesta
- Monolito Django modular: `catalog`, `inventory`, `customers`, `orders`, `checkout`, `dashboard`.
- Postgres (prod), Redis (cache/sesión), Celery (emails/PDF async).
- Front híbrido: templates Django + JS liviano con fetch a endpoints.

## OUTPUT 2 — Diseño técnico

## Diagrama textual de arquitectura
- Browser → Django Templates/API
- Django Apps → Postgres
- Django/Celery → Redis (broker/cache)
- Celery workers → Email/PDF jobs
- Checkout → PaymentGateway (interfaz) + DummyGateway
- Fallback: WhatsApp checkout

## Entidades (ASCII)
```
Category 1---* Product 1---* ProductVariant 1---1 StockLevel
Product 1---* ProductImage
ProductVariant 1---* InventoryMovement

Customer 1---* Address
Customer 1---* Cart 1---* CartItem *---1 ProductVariant
Customer 1---* Order 1---* OrderItem *---1 ProductVariant
Order 1---* OrderStatusHistory
Order *---0..1 Coupon
```

## Índices recomendados
- Product: `(slug)`, `(is_active, created_at)`
- ProductVariant: `(sku)`, `(product_id, size, color)`
- Order: `(status, created_at)`
- InventoryMovement: `(variant_id, created_at)`
- Cart: `(session_key)`

## Endpoints/rutas MVP
- Web: `/`, `/collection/`, `/product/<slug>/`, `/cart/`, `/checkout/`, `/order/<id>/confirmation/`
- API: `/api/products`, `/api/cart/items`, `/api/checkout/quote`, `/api/checkout/confirm`
- Fallback: `/checkout/whatsapp/`

## Flujo principal
1. Ver catálogo + filtros.
2. Seleccionar variante y añadir al carrito.
3. Checkout captura datos cliente/dirección/cupón.
4. `create_order_from_cart()` valida stock con `select_for_update`.
5. Crea `Order/OrderItem`, descuenta stock, guarda `InventoryMovement`.
6. Dispara email + PDF (mock/async).
7. Render confirmación + CTA WhatsApp como fallback.

## OUTPUT 4 — Mejora UX/UI (objetivo y checklist)

### Cambios de UI implementados en este MVP
- Sistema visual base premium (`perle.css`) con tipografía editorial y cards limpias.
- Grid responsive mobile-first.
- Hero con jerarquía clara y tono de marca.

### Definition of Done del front (checklist)
- [ ] Responsive mobile/tablet/desktop
- [ ] Navegación por teclado y focus visible
- [ ] Sin errores en consola
- [ ] Imágenes lazy-load
- [ ] Lighthouse básico (Perf/Acc/Best Practices)
