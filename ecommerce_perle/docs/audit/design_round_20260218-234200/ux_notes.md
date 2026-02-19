# UX Notes (Baseline)

- Falta menú móvil colapsable dedicado; la navegación simplemente envuelve y reduce claridad en 360px.
- No hay meta description/OG tags en `base.html`, lo que limita consistencia SEO/social.
- Design tokens existen pero no siguen el contrato solicitado (`--s-*`, `--r-*`, estados semánticos completos).
- Biblioteca de componentes no está completa (faltan `card-header`, `card-body`, `pill`, `chip`, `divider`, `modal`, alertas tipadas consistentes).
- Sistema de toast actual no maneja stack ni tipos visuales; un único nodo limita feedback concurrente.
- Home no incluye trust bar explícita ni bloques editoriales separados de destacados/nuevas/colecciones.
- Product detail no ofrece galería de thumbs ni bloque de productos relacionados.
- Selector visual de variantes y estado low-stock no están claramente diferenciados por UI semántica.
- Cart no muestra miniatura de producto ni botón explícito para aplicar cupón con feedback inmediato.
- Checkout no muestra spinner visual dedicado en botón (solo cambio de texto) ni alertas diferenciadas por severidad.
- Legal pages son legibles pero pueden mejorar ritmo tipográfico y estructura de lectura larga.
- Hay inconsistencias de clase entre controles (`input/select`) y sistema utilitario esperado (`.input/.select/.textarea`).
