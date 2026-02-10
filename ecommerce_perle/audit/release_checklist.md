# Release Checklist

## Estado por fase
- Fase 1 (Preparación y reproducibilidad): **PARCIAL / BLOQUEADA POR ENTORNO**
  - OK: baseline capturado en `audit/00_env/`.
  - Bloqueo: instalación limpia de deps en `.venv_audit` falló por red (`BLOCKER-BOOT-001`).
  - Bloqueo: `runserver` no permitido por socket (`BLOCKER-BOOT-002`).
- Fase 2 (Smoke funcional): **OK (vía Django test client)**
  - Evidencia: `audit/02_smoke/smoke_flows.log`.
- Fase 3 (Análisis estático): **PARCIAL**
  - OK: `check`, `check --deploy`, `test`, `compileall`, fallback secrets/SAST.
  - Bloqueo: tooling automatizada SAST/CVE/coverage no instalable por red.
- Fase 4 (Revisión manual AppSec): **OK**
  - Evidencia: `audit/04_appsec_review/manual_review.md`.
- Fase 5 (DAST + manual): **OK (vía test client)**
  - Evidencia pre/post fix en `audit/05_dast/`.
- Fase 6 (Regresión y estabilidad): **OK**
  - `python manage.py test` => 19/19 OK (`audit/06_regression/tests_after_csrf_fix.log`).
- Fase 7 (Entregables): **OK**
  - `audit/final_report.md`, `audit/release_checklist.md`, `audit/commands.log`.

## Gate de severidad
- CRITICAL abiertos: **0**
- HIGH abiertos: **0**

## Veredicto
**NO APTO**

### Justificación
Aunque no quedan CRITICAL/HIGH abiertos en código, el proceso de auditoría/release no cierra completamente por bloqueos de entorno que impiden:
1. Reproducibilidad total de instalación limpia.
2. Ejecución de toolchain automatizada de CVE/SAST/coverage requerida por el plan.

## Acciones requeridas para pasar a APTO
1. Ejecutar auditoría en entorno con salida a internet para instalar y correr `bandit`, `semgrep`, `pip-audit`, `coverage`.
2. Repetir pipeline de evidencias con esos reportes anexos en `audit/03_static/`.
3. Confirmar que no aparezcan hallazgos CRITICAL/HIGH adicionales.
