# Perle Swimwear Landing

Repositorio canónico del storefront y la operación de Perle Swimwear.

## Fuente de verdad
- Runtime deployable: [`ecommerce_perle/`](./ecommerce_perle)
- Blueprint de Render: [`render.yaml`](./render.yaml)
- Frontend y flujo real de compra: templates y assets dentro de `ecommerce_perle`

## Qué no se despliega
- [`legacy/`](./legacy) conserva material histórico y referencias visuales.
- Nada dentro de `legacy/` es canónico, soportado ni parte del deploy actual.

## Arranque local
```bash
cd ecommerce_perle
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python manage.py migrate --noinput
python manage.py seed_demo
python manage.py runserver
```

## Validación mínima
```bash
cd ecommerce_perle
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --noinput
ruff check .
```

## Documentación activa
- Runtime y setup detallado: [`ecommerce_perle/README.md`](./ecommerce_perle/README.md)
- Operación: [`ecommerce_perle/docs/RUNBOOK.md`](./ecommerce_perle/docs/RUNBOOK.md)
- QA manual: [`ecommerce_perle/docs/QA_CHECKLIST.md`](./ecommerce_perle/docs/QA_CHECKLIST.md)

## Estado operativo
- Staging-ready: sí, con CI visible, `healthz` y release flow separado del proceso web.
- Producción pequeña/mediana: condicionada a configurar variables reales, revisar CVE desde CI y ejecutar smoke post-deploy.
