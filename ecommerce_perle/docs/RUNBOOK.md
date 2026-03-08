# Runbook Operativo - Perle E-commerce

## 1. Arranque local
```bash
source .venv/bin/activate
python manage.py migrate --noinput
python manage.py runserver
```

## 2. Comandos de salud
```bash
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
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

## 6. Validación pre-release
```bash
python manage.py check
DEBUG=0 DJANGO_SECRET_KEY='long-secret-50-plus-characters' ALLOWED_HOSTS='perle-ecommerce.onrender.com' CSRF_TRUSTED_ORIGINS='https://perle-ecommerce.onrender.com' DATABASE_URL='sqlite:///db.sqlite3' python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py test
ruff check .
bandit -q -r apps core -lll
pip-audit -r requirements.txt
semgrep --config p/django --config p/python apps core
```

Notas operativas:
- La auditoria CVE canónica es el job CI (`quality-and-security`) que publica `pip-audit.json`.
- En local sin salida a internet, `pip-audit` puede fallar por DNS/red.
- Para redes corporativas, configurar `PIP_INDEX_URL` y/o `PIP_EXTRA_INDEX_URL` hacia mirror interno.
- Estrés PostgreSQL local reproducible: `bash scripts/qa/run_pg_stress.sh`.

## 7. Seguridad por fases (monitor -> enforce)
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

## 8. Rollback básico
1. Revertir despliegue al release anterior en plataforma.
2. Restaurar DB snapshot si hubo migración conflictiva.
3. Ejecutar smoke test de 10 minutos.
4. Registrar incidente y causa raíz.
