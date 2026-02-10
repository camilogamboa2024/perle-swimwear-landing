# BLOCKER-BOOT-001

## Title
No se pudo completar instalación limpia en `.venv_audit` por restricción de red (DNS/proxy sin salida a PyPI).

## Evidence
- Ver: `audit/01_boot/pip_install_requirements.log`
- Error principal: `Failed to establish a new connection` y `No matching distribution found` por imposibilidad de resolver `pypi`.

## Impact
Impide reproducir `pip install -r requirements.txt` desde cero en este sandbox.

## Mitigation / Fix applied
Se utiliza entorno ya provisionado `.venv` (local) para ejecutar el resto de validaciones (check/test/smoke/AppSec) y mantener trazabilidad completa en `audit/`.
