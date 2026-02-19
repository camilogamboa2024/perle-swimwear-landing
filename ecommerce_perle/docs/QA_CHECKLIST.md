# QA Checklist Manual

## Alcance
- Storefront público (templates + `perle.css` + `storefront.js`).
- Panel admin premium operativo (Jazzmin + overrides + assets `static/admin/*`).

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

## Admin Premium (es-ES)
1. Login admin (`/admin/login/`)
- Renderiza texto en español (`Iniciar sesión`, `Nombre de usuario`, `Contraseña`).
- Estilo luxury dark-slate aplicado.
2. Dashboard admin (`/admin/`)
- Renderiza KPIs completos: hoy, semana, pendientes, stock bajo, ingresos, ticket promedio.
- Renderiza gráficos sin errores JS.
- Muestra bloques de pendientes, alertas de inventario y top productos.
3. Órdenes (`/admin/orders/order/`)
- Changelist con badges de estado.
- Filtro rápido por período (`Hoy`, `Esta semana`, `Solo pendientes`) operativo.
- Acciones masivas (`paid/shipped/delivered/cancelled`) muestran pantalla de confirmación premium.
4. Inventario (`/admin/inventory/stocklevel/`)
- Changelist con alerta visual (`Crítico/Bajo/Saludable`).
- Acción `Ajustar stock` muestra proyección por variante.
- Al aplicar ajuste, crea `InventoryMovement` tipo `ADJUST`.
5. Catálogo / Clientes / Cupones
- Catálogo con previews, estado visual y form más estructurado.
- Clientes con métricas (`total comprado`, `último pedido`, historial enlazado).
- Cupones con badges de vigencia (`Vigente/Por vencer/Expirado`) y filtros.
6. Seed demo (`/admin/ops/seed-demo/`)
- Disponible solo con setting habilitado.
- Pantalla de confirmación muestra warning operativo.
