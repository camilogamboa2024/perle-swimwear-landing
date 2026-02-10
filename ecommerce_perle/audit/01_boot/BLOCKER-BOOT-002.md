# BLOCKER-BOOT-002

## Title
No fue posible levantar `runserver` en el sandbox local por restricción de permisos de socket (`Errno 1 Operation not permitted`).

## Evidence
- Ver `audit/01_boot/runserver.log`.

## Impact
Impide pruebas HTTP por puerto local con `curl` contra `127.0.0.1:8000`.

## Mitigation / Workaround used
Se ejecuta testing dinámico equivalente mediante `django.test.Client` y `Client(enforce_csrf_checks=True)` para generar evidencia de request/response y validar controles AppSec (CSRF, IDOR, auth bypass, etc.) sin depender de bind de socket.
