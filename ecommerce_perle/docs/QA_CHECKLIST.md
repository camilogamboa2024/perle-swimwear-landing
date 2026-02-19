# QA Checklist Manual (Storefront UI)

## Alcance
- Solo storefront público (templates + `perle.css` + `storefront.js`).
- Sin validación de panel admin en este checklist.

## Navegadores y viewport
- Chrome desktop (`1280x800` o superior).
- Firefox desktop.
- Mobile `360x800` (emulación).

## Flujo de compra (no regresión)
1. Home (`/`)
- Hero, trust bar y cards cargan sin overflow.
- CTA `Comprar ahora` baja a `#catalogo-section`.
- Botones `Añadir` agregan productos y actualizan badge.
2. Carrito (`/cart/`)
- Stepper `− / +` actualiza cantidad.
- `Eliminar` borra item.
- `Vaciar carrito` deja estado vacío visible.
- Input de cupón guarda feedback visual.
3. Checkout (`/checkout/`)
- Labels y helpers visibles.
- Botón muestra estado `Procesando...` con spinner.
- Errores de validación/cupón aparecen en alert/toast.
4. Confirmación (`/orders/confirmation/<uuid>/`)
- `public_id`, total e items visibles.
- CTA WhatsApp solo aparece cuando hay teléfono configurado.

## WhatsApp opcional (obligatorio)
1. `WHATSAPP_PHONE=""`
- No aparece FAB.
- No aparece ningún enlace `wa.me` en home/footer/confirmación.
2. `WHATSAPP_PHONE=573001234567` (ejemplo)
- FAB visible.
- Enlaces `wa.me/573001234567` válidos en footer/confirmación.

## Accesibilidad
1. Navegación por teclado:
- `Tab` recorre header, cards, carrito y checkout.
- `Enter` funciona en botones y links críticos.
2. Focus visible:
- Botones, links, inputs y select muestran `:focus-visible`.
3. Touch targets:
- Controles interactivos >= `44px` en mobile.
4. Contraste:
- Texto base y CTA principales mantienen legibilidad AA.

## Performance visual
1. Listados con `loading="lazy"` en imágenes.
2. Cards y detalle reservan espacio con `aspect-ratio` (sin CLS notorio).
3. JS sin dependencias externas ni bloqueos visibles en interacción base.
