# AGENTS.md

## Rutas canónicas
- Aplicación deployable: `ecommerce_perle/`
- Blueprint de plataforma: `render.yaml`
- Material histórico no canónico: `legacy/`

## Comandos de validación
```bash
cd ecommerce_perle
python manage.py check
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --noinput
ruff check .
npm run test:e2e:qa
```

## Reglas del repo
- No tratar `legacy/` como frontend activo ni base de deploy.
- Mantener Panamá-first, moneda USD y persistencia `country='Panama'` en el runtime canónico.
- No introducir claims en README/docs que no estén respaldados por validación ejecutada.
- Priorizar cambios pequeños, reversibles y auditables.

## Definición de done
- Cambio implementado y justificado.
- Validación razonable ejecutada.
- Sin regresión del flujo crítico de compra.
- Documentación alineada con la realidad.

