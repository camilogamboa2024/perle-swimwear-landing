# QA Checklist Manual

## Navegadores y viewport
- Chrome (desktop)
- Firefox (desktop)
- Mobile 360px (emulación)

## Flujo principal e-commerce
1. Home:
   - cards premium visibles
   - CTA "Añadir a bolsa" funcional
2. Carrito:
   - incrementar/disminuir cantidad
   - eliminar item
   - vaciar carrito
3. Checkout:
   - validación de campos requeridos
   - estado `Procesando...` al enviar
   - mensaje claro en errores
4. Confirmación:
   - `public_id` visible
   - total correcto
   - items listados

## WhatsApp opcional
1. `WHATSAPP_PHONE=""`:
   - sin FAB
   - sin enlaces `wa.me` en home/footer/confirmación
2. `WHATSAPP_PHONE` con número:
   - FAB visible
   - enlaces `wa.me` válidos

## Casos de error
1. Stock insuficiente al agregar/actualizar cantidad -> `400` + mensaje.
2. Checkout con carrito vacío -> `400` + mensaje controlado.
3. Cupón inválido o expirado -> `400`, código `invalid_coupon`.

## Seguridad funcional
1. Mutaciones de carrito sin CSRF -> `403`.
2. Confirm checkout sin CSRF -> `403`.
3. Confirmación de orden con sesión distinta -> `404`.

## Admin operativo
1. Dashboard con KPIs en home admin.
2. Acciones masivas en órdenes con confirmación:
   - paid
   - shipped
   - delivered
   - cancelled
3. Ajuste masivo de stock:
   - actualiza `StockLevel`
   - crea `InventoryMovement(ADJUST)`
4. Botón `Seed demo`:
   - visible solo en `DEBUG=1`
   - oculto/no accesible en `DEBUG=0`

## Accesibilidad básica
1. Navegación por teclado (Tab) en header/cart/checkout.
2. Focus visible en botones e inputs.
3. Contraste legible en texto y CTA principales.
