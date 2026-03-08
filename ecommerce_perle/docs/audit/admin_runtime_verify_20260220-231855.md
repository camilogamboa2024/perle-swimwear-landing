# Verificación runtime admin (20260220-231855)

## Proceso activo
38982 .venv/bin/python manage.py runserver 127.0.0.1:8001
39004 /home/kicksdoors/Desktop/perle-swimwear-landing/ecommerce_perle/.venv/bin/python manage.py runserver 127.0.0.1:8001
310952 /bin/bash -c cd /home/kicksdoors/Desktop/perle-swimwear-landing/ecommerce_perle TS=$(date +%Y%m%d-%H%M%S) OUT="docs/audit/admin_runtime_verify_${TS}.md" COOKIE=/tmp/perle_admin_cookie.txt rm -f "$COOKIE"  curl -s -c "$COOKIE" http://127.0.0.1:8001/admin/login/ > /tmp/perle_admin_login_get.html CSRF=$(awk '/csrftoken/ {print $7}' "$COOKIE" | tail -n1)  curl -s -L -b "$COOKIE" -c "$COOKIE" -e http://127.0.0.1:8001/admin/login/ \   -d "username=admin_capture&password=<redacted>&csrfmiddlewaretoken=${CSRF}&next=/admin/" \   http://127.0.0.1:8001/admin/login/ > /tmp/perle_admin_after_login.html  {   echo "# Verificación runtime admin (${TS})"   echo   echo "## Proceso activo"   pgrep -af "manage.py runserver" || true   echo   echo "## Login admin (curl)"   curl -s http://127.0.0.1:8001/admin/login/ | rg -n "bootswatch/flatly/bootstrap.min.css|admin/perle_admin_v2.css|admin/perle_admin.js|Iniciar sesión" || true   echo   echo "## CSS v2 (inicio)"   curl -s http://127.0.0.1:8001/static/admin/perle_admin_v2.css | head -n 20   echo   echo "## Admin autenticado (curl + cookie)"   rg -n "perle-admin-dashboard|Operación diaria en tiempo real|admin/perle_dashboard_v2.js" /tmp/perle_admin_after_login.html || true } > "$OUT"  echo "$OUT"

## Login admin (curl)
16:    <title>Iniciar sesión | Administración Perle</title>
26:        <link rel="stylesheet" href="/static/vendor/bootswatch/flatly/bootstrap.min.css" id="jazzmin-theme" />
36:    <link rel="stylesheet" href="/static/admin/perle_admin_v2.css">
173:    <h1>Iniciar sesión</h1>
194:        <input type="submit" value="Iniciar sesión">
237:<script src="/static/admin/perle_admin.js"></script>

## CSS v2 (inicio)
:root {
  --perle-bg: #f4f8fb;
  --perle-surface: #ffffff;
  --perle-surface-2: #eef4f8;
  --perle-surface-soft: #f8fcfe;
  --perle-border: #d6e3ec;
  --perle-text: #173447;
  --perle-muted: #5f7787;
  --perle-primary: #0f8fb2;
  --perle-primary-700: #0a6f8b;
  --perle-pearl: #f2dfbf;
  --perle-success: #2f8f62;
  --perle-warning: #a1701a;
  --perle-danger: #b24a57;
  --perle-info: #2b78b2;
  --perle-shadow-sm: 0 8px 20px rgba(16, 51, 72, 0.08);
  --perle-shadow-md: 0 14px 34px rgba(16, 51, 72, 0.12);
  --perle-radius-md: 12px;
  --perle-radius-lg: 16px;
  --perle-radius-xl: 20px;

## Admin autenticado (curl + cookie)
317:<section class="perle-admin-dashboard">
321:      <h1>Operación diaria en tiempo real</h1>
1021:<script src="/static/admin/perle_dashboard_v2.js"></script>
