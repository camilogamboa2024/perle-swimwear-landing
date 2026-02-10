# Performance Básico (Funcional)

## Metodología
- Medición simple con `CaptureQueriesContext` (Django test client, entorno local).
- Endpoints medidos:
  - `/`
  - `/api/products/`
  - `/api/cart/`
  - `/checkout/api/checkout/confirm/`

## Resultado
| Endpoint | Status | Queries |
|---|---:|---:|
| `/` | 200 | 3 |
| `/api/products/` | 200 | 3 |
| `/api/cart/` | 200 | 13 |
| `/checkout/api/checkout/confirm/` | 201 | 23 |

Fuente: `test-results/performance_queries.log`

## Conclusiones
- No se observaron cuelgues ni timeouts en rutas críticas.
- No hay evidencia de N+1 severo en catálogo/API de productos.
- `api/cart` y `checkout confirm` tienen varias consultas por composición de datos y transacción; aceptable para MVP, pero optimizable en futuras iteraciones.
