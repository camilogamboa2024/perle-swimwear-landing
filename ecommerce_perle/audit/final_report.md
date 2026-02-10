# Reporte Final de Auditoría AppSec + QA

## Alcance ejecutado
- Baseline y reproducibilidad en repo local actual.
- Smoke funcional de flujos críticos.
- Revisión estática y manual AppSec.
- DAST manual (con `django.test.Client` por bloqueo de socket en sandbox).
- Fix inmediato de hallazgos HIGH detectados + re-test + regresión.

## Tabla de hallazgos
| ID | Severidad | Componente | Descripción | Impacto | Pasos reproducción | Evidencia | Fix aplicado (PR/commit) | Test agregado | Estado | Riesgo residual |
|---|---|---|---|---|---|---|---|---|---|---|
| APPSEC-001 | HIGH | `apps/orders/views.py`, `apps/checkout/views.py` | CSRF bypass en endpoints mutables de carrito/checkout (aceptaban requests sin token). | Ejecución de acciones sensibles por sitios terceros en sesión de víctima. | 1) `Client(enforce_csrf_checks=True)` 2) `POST /api/cart/items/` sin token 3) `POST /checkout/api/checkout/confirm/` sin token. | Pre-fix: `audit/05_dast/dast_manual_round1.log`, `audit/05_dast/csrf_cart_mutations_round1.log` (status 201/200 sin CSRF). Post-fix: `audit/05_dast/dast_manual_round2.log`, `audit/05_dast/csrf_cart_mutations_round2.log` (status 403 sin CSRF). | Se añadió `core/authentication.py` (`EnforcedCsrfSessionAuthentication`) y se aplicó en vistas mutables: `apps/orders/views.py`, `apps/checkout/views.py`. Diff: `audit/07_release/security_fixes.diff`. | Sí: `apps/orders/tests.py` (`CartApiCsrfTest`), `apps/checkout/tests.py` (`test_checkout_confirm_requires_csrf_token`). | Cerrado | Bajo |
| REL-001 | MEDIUM | Bootstrapping entorno limpio | No se pudo instalar dependencias en `.venv_audit` por restricción de red (PyPI inaccesible). | Limita reproducibilidad total “from scratch” en este sandbox. | Ejecutar `pip install -r requirements.txt` en `.venv_audit`. | `audit/01_boot/pip_install_requirements.log`, `audit/01_boot/BLOCKER-BOOT-001.md`. | Mitigación: ejecución de auditoría en `.venv` provisionado localmente. | N/A | Abierto (entorno) | Medio |
| REL-002 | MEDIUM | Ejecución dinámica HTTP por socket | `runserver` no pudo bindear puerto en sandbox (`Errno 1`). | Impide validación por `curl` contra `127.0.0.1:8000`. | Ejecutar `python manage.py runserver 127.0.0.1:8000 --noreload`. | `audit/01_boot/runserver.log`, `audit/01_boot/BLOCKER-BOOT-002.md`. | Mitigación: DAST equivalente con `django.test.Client` + evidencia request/response en `audit/05_dast/`. | N/A | Abierto (entorno) | Medio |
| APPSEC-002 | LOW | Hardening (`core/settings.py`) | `SECURE_HSTS_PRELOAD` por defecto en `0` (warning deploy). | Hardening incompleto para preload list. | Ejecutar `DEBUG=0 ... python manage.py check --deploy`. | `audit/06_regression/check_deploy_debug0_longkey.log` (`security.W021`). | No se cambió default en esta auditoría (requiere decisión de dominio/subdominios y política HSTS). | N/A | Abierto | Bajo |
| TOOL-001 | MEDIUM | Tooling de seguridad | No disponibles `bandit/semgrep/pip-audit/coverage` y no fue posible instalarlos por bloqueo de red. | Reduce profundidad de evidencia automatizada SAST/CVE/coverage. | Verificar disponibilidad y ejecutar instalación en `.venv`. | `audit/03_static/tool_availability.txt`, `audit/03_static/pip_install_security_tools.log`. | Fallback manual aplicado (`rg` SAST/secrets + `pip check` + revisión manual). | N/A | Abierto (entorno) | Medio |

## Evidencia funcional (smoke)
- Smoke principal: `audit/02_smoke/smoke_flows.log`
- Admin smoke: `audit/02_smoke/admin_login_check.log`, `audit/02_smoke/admin_home_snippet.log`
- Resultado: flujos críticos funcionales en local (con workaround de entorno).

## Evidencia de calidad/regresión
- `audit/03_static/check.log`
- `audit/03_static/tests.log`
- `audit/06_regression/tests_after_csrf_fix.log` (19 tests OK)
- `audit/06_regression/check_after_fix.log`
- `audit/06_regression/makemigrations_check_after_fix.log`

## Entregable B (fixes + tests)
En repositorio local (sin PR remoto):
- Fix code diff: `audit/07_release/security_fixes.diff`
- Nuevos tests de regresión:
  - `apps/orders/tests.py`
  - `apps/checkout/tests.py`
- Estado git final: `audit/07_release/git_status_short_final.txt`

## Veredicto final
**NO APTO**

### Motivos exactos
1. Quedan bloqueos operativos de auditoría completa en entorno (`REL-001`, `REL-002`) que impiden reproducibilidad 100% from-scratch + HTTP socket testing tradicional.
2. No fue posible ejecutar toolchain SAST/CVE/cobertura automatizada por restricciones de red (`TOOL-001`), por lo que el gate de supply-chain no queda completamente cerrado.

> Nota: no quedan hallazgos CRITICAL/HIGH abiertos en código tras los fixes aplicados y re-validados.
