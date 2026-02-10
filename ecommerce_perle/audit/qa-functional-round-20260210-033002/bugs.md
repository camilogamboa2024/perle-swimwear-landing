# Bugs — QA Functional Round

## Resumen
- Total hallazgos: 1
- Cerrados: 1
- Abiertos: 0

## Detalle
| ID | Severidad | Módulo | Estado | Descripción corta |
|---|---|---|---|---|
| QA-BUG-001 | HIGH | `apps/orders` | Cerrado | 500 en `/cart/` cuando usuario auth tiene email ya usado por customer guest |

### QA-BUG-001 (Cerrado)
- Reproducción:
1. Crear `Customer` guest con email `qa-collision@example.com`.
2. Crear `User` autenticable con el mismo email.
3. Login y `GET /cart/`.
- Resultado actual (antes): 500 por `UNIQUE constraint failed: customers_customer.email`.
- Resultado esperado: 200 y customer reutilizado/ligado sin romper flujo.
- Evidencia antes fix: `test-results/bug_repro_customer_email_collision.log`.
- Fix aplicado:
  - Reuso seguro de customer por `email/user` y fallback de email único si hay colisión no reasignable.
  - Archivo: `apps/orders/views.py`.
- Test de regresión:
  - `AuthenticatedCustomerReuseTest`.
  - Archivo: `apps/orders/tests.py`.
- Evidencia post-fix: `test-results/bug_repro_customer_email_collision_after_fix.log`.
