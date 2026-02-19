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
```

## 7. Rollback básico
1. Revertir despliegue al release anterior en plataforma.
2. Restaurar DB snapshot si hubo migración conflictiva.
3. Ejecutar smoke test de 10 minutos.
4. Registrar incidente y causa raíz.
