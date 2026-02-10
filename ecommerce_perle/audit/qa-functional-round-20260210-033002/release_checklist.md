# Release Checklist — QA Functional

## Fase 0 — Control y trazabilidad
- [x] Branch QA creada (`qa/functional-audit`)
- [x] Carpeta de ronda QA creada
- [x] Baseline capturado (`git status`, `python --version`, `pip freeze`, commit)

## Fase 1 — Build & smoke
- [x] Migraciones en verde
- [x] Seed demo en verde
- [x] `check` en verde
- [x] Smoke funcional rutas críticas en verde

## Fase 2 — Mapa del sistema
- [x] `system-map.md` generado

## Fase 3 — Diseño de casos
- [x] `test-plan.md` generado

## Fase 4 — Unit + integration
- [x] Tests de módulos críticos ejecutados
- [x] Suite completa ejecutada (`24 tests OK`)
- [x] Test de regresión agregado para bug HIGH

## Fase 5 — E2E funcional
- [x] E2E vía `django.test.Client` ejecutado y evidenciado

## Fase 6 — Bug hunt
- [x] Inputs inválidos/límites/reintentos ejecutados
- [x] Sin 500 en rutas críticas auditadas

## Fase 7 — Calidad de errores
- [x] Errores funcionales devueltos como 4xx controlados

## Fase 8 — Performance básico
- [x] Query-count de endpoints calientes documentado

## Fase 9 — Bug fix loop
- [x] Bug registrado
- [x] Repro antes fix
- [x] Fix aplicado
- [x] Test de regresión
- [x] Re-test post-fix

## Veredicto final
- **APTO**
- Justificación: No quedan BLOCKER/CRITICAL/HIGH abiertos tras fix + regresión verde.
