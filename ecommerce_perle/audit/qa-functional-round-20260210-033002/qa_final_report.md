# QA Final Report — Functional Audit (Local)

## Contexto ejecutado
- Repo: `/home/kicksdoors/Desktop/perle-swimwear-landing/ecommerce_perle`
- Branch: `qa/functional-audit`
- Base commit: `1d3e0be`
- Suite final: `24` tests en verde
- Evidencia de comandos: `commands.log`

## Tabla de hallazgos
| ID | Severidad | Módulo | Descripción | Pasos | Esperado | Actual (antes fix) | Evidencia | Fix (commit/PR) | Test agregado | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
| QA-BUG-001 | HIGH | `apps/orders` | Colisión de email entre customer guest y user auth produce 500 en `/cart/` | Crear customer guest + user con mismo email, login y abrir `/cart/` | 200 sin error y customer ligado correctamente | 500 `UNIQUE constraint failed: customers_customer.email` | `test-results/bug_repro_customer_email_collision.log` | Local branch `qa/functional-audit` (fix en `apps/orders/views.py`) | `AuthenticatedCustomerReuseTest` en `apps/orders/tests.py` | Cerrado |

## Verificaciones ejecutadas
- Build/checks: `migrate`, `seed_demo`, `check`, `check --deploy`.
- Smoke E2E funcional (client): home/catalog/cart/checkout/confirm/legal/admin.
- Bug hunt: inválidos, límites, IDs inexistentes, doble submit.
- Regresión: suite completa `python manage.py test`.
- Coverage operacional: `python -m trace --count --summary manage.py test`.

## Cobertura
- `trace` reportó ejecución en módulos de `apps.*` y `core.*` con resumen disponible en:
  - `test-results/trace_coverage.log`
  - `test-results/trace_coverage_project_summary.log`
- Nota: esta métrica es de `trace` stdlib (menos estricta que `coverage.py` para branch coverage).

## Resultado de release QA
- BLOCKER abiertos: `0`
- CRITICAL abiertos: `0`
- HIGH abiertos: `0`
- Veredicto: **APTO**

## Riesgo residual
- Métrica de cobertura basada en `trace` (stdlib) por restricción de red para instalar `coverage.py`; recomendable revalidar en CI con `coverage.py` cuando haya conectividad.
