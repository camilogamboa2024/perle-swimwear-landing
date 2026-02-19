# Runtime Baseline Storefront (2026-02-19)

## Objetivo
Estabilizar entorno local para evitar resultados visuales inconsistentes por múltiples procesos `runserver`.

## Acciones ejecutadas
1. Se identificaron varios procesos `python manage.py runserver` en puertos `8001`, `8002`, `8012`, `8013`, `8016`, `8018`, `8022`.
2. Se detuvieron procesos duplicados y se dejó una sola instancia para auditoría en `127.0.0.1:8001`.
3. Se verificó respuesta SSR de `/`:
   - `status=200`
   - referencia de branding activa `brand/perle-wordmark.png`
   - referencia de estilos `css/perle.css`

## Evidencia baseline previa al ajuste final
- `docs/screenshots/home_desktop_before.png`
- `docs/screenshots/home_mobile360_before.png`
