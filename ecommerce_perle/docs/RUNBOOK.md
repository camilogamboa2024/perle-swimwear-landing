# Runbook Operativo - Perle E-commerce

## 1. Arranque local
```bash
source .venv/bin/activate
python manage.py migrate --noinput
python manage.py runserver
```

Nota operativa:
- Si `runserver` avisa migraciones pendientes, la DB local persistente quedó atrasada; eso no implica inconsistencia del repo. Ejecuta `python manage.py migrate --noinput` sobre el entorno local antes del smoke manual.

## 2. Comandos de salud
```bash
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
```

Healthcheck HTTP:
```bash
curl -fsS http://127.0.0.1:8000/healthz/
```

## 3. Operación diaria en admin
1. Revisar dashboard (`/admin/`) para:
   - órdenes del día/semana
   - bajo stock
   - ingresos semanales
   - todos los montos en USD (base interna en centavos)
2. Procesar órdenes pendientes:
   - usar acciones masivas para pasar a `paid` / `shipped` / `delivered`.
3. Inventario:
   - entrar a `Stock levels`
   - usar acción `Ajustar stock` con motivo obligatorio.
4. Cupones:
   - activar/desactivar
   - revisar expiraciones.

## 4. Seed demo (solo dev/staging)
- Disponible en admin cuando `DEBUG=1`.
- Ruta: `/admin/ops/seed-demo/`.
- En producción (`DEBUG=0`) la ruta devuelve `404`.

## 5. Incidentes frecuentes

### 5.1 `Cupón inválido o expirado`
- Validar en admin:
  - `is_active=True`
  - `expires_at` en el futuro o vacío.

### 5.2 `Sin stock para SKU`
- Revisar `StockLevel` de la variante.
- Ajustar con acción masiva y registrar motivo.

### 5.3 `403 CSRF` en frontend
- Verificar que:
  - existe cookie `csrftoken`
  - request incluye `X-CSRFToken`
  - `CSRF_TRUSTED_ORIGINS` incluye dominio frontend.

### 5.4 Direcciones históricas con país inconsistente
- Desde esta versión, el checkout nuevo persiste `country='Panama'`.
- No se hizo backfill masivo sobre datos previos para no reescribir histórico legítimo.
- Si detectas pedidos antiguos creados con `country='Colombia'` por el default anterior, corrígelos manualmente en admin solo después de validar el contexto real del pedido.

## 6. Validación pre-release
```bash
python manage.py check
DEBUG=0 DJANGO_SECRET_KEY='long-secret-50-plus-characters' ALLOWED_HOSTS='perle-ecommerce.onrender.com' CSRF_TRUSTED_ORIGINS='https://perle-ecommerce.onrender.com' DATABASE_URL='sqlite:///db.sqlite3' python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py test
coverage run manage.py test && coverage report
ruff check .
bandit -q -r apps core -lll
pip-audit -r requirements.txt
semgrep --config p/django --config p/python apps core
```

Notas operativas:
- La auditoria CVE canónica es el job CI (`quality-and-security`) que publica `pip-audit.json`.
- Coverage visible canónica: el mismo job publica `coverage.txt` y `coverage.xml`.
- En local sin salida a internet, `pip-audit` puede fallar por DNS/red.
- Para redes corporativas, configurar `PIP_INDEX_URL` y/o `PIP_EXTRA_INDEX_URL` hacia mirror interno.
- Estrés PostgreSQL local reproducible: `bash scripts/qa/run_pg_stress.sh`.
- `semgrep` excluye `.venv*`, `staticfiles/` y `audit/`.
- Los dos templates admin con falso positivo documentado por parsing Django/CSRF usan `nosemgrep` puntual. Eso reduce ruido sin aceptar riesgo en el runtime canónico.

## 7. Deploy en Render
- `buildCommand`: instala dependencias y corre `collectstatic`.
- `preDeployCommand`: corre migraciones antes de arrancar el proceso web.
- `startCommand`: arranca Gunicorn sin migrar en runtime.
- `healthCheckPath`: `/healthz/`.
- `autoDeployTrigger: checksPass`: el deploy automático espera CI verde.
- Estado actual: release candidate listo para validación externa, pero staging y producción siguen sin declararse desde esta sesión.
- Última verificación pública del dominio Render documentado: `404 no-server`.
## 8. Seguridad por fases (monitor -> enforce)
Fase monitor (recomendada en arranque):
```bash
export SECURITY_PHASE=monitor
export ADMIN_MFA_REQUIRED=0
export AXES_FAILURE_LIMIT=8
```

Fase enforce (cuando reportes estables):
```bash
export SECURITY_PHASE=enforce
export ADMIN_MFA_REQUIRED=1
export AXES_FAILURE_LIMIT=5
```

Validación dinámica (servidor activo):
```bash
mkdir -p audit/security_round_local
python scripts/security/dast_auth_csrf.py --base-url http://127.0.0.1:8000 --out audit/security_round_local/dast_auth_csrf.json --failure-limit "${AXES_FAILURE_LIMIT:-8}" --scope web
python scripts/security/verify_security_headers.py --base-url http://127.0.0.1:8000 --out audit/security_round_local/security_headers.json --phase "${SECURITY_PHASE:-monitor}" --scope web --dast-report audit/security_round_local/dast_auth_csrf.json
python scripts/security/gate_security.py --input-dir audit/security_round_local --out audit/security_round_local/security_gate_summary.json --markdown audit/security_round_local/security_gate_summary.md --strict-critical-high
```

Resultado esperado de gate:
- `critical = 0`
- `high = 0`

## 9. Smoke post-deploy
1. `curl -fsS https://<tu-dominio>/healthz/`
2. Cargar `/` y agregar un producto al carrito.
3. Confirmar un checkout en staging.
4. Verificar `/orders/confirmation/<uuid>/` en la misma sesión.
5. Entrar a `/admin/` y validar KPIs + login.

## 10. Rollback básico
1. Revertir despliegue al release anterior en plataforma.
2. Restaurar DB snapshot si hubo migración conflictiva.
3. Ejecutar smoke test de 10 minutos.
4. Registrar incidente y causa raíz.

## 11. Criterio de entorno
- Demo: apto.
- Listo para validación externa: sí.
- Staging serio: pendiente de verificación externa en GitHub/Render.
- Producción pequeña/mediana: no declarada.
