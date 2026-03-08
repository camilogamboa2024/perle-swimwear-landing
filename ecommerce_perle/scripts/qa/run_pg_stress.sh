#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUT_DIR="${QA_OUTPUT_DIR:-$ROOT_DIR/audit/pg_stress_${TIMESTAMP}}"
mkdir -p "$OUT_DIR"

USE_DOCKER_POSTGRES="${USE_DOCKER_POSTGRES:-1}"
QA_PORT="${QA_PORT:-8011}"
STOCK_CAP="${STOCK_CAP:-20}"
ADMIN_USER="${QA_ADMIN_USER:-qa_admin}"
ADMIN_PASS="${QA_ADMIN_PASS:-AdminPass123!}"

PG_IMAGE="${PG_IMAGE:-postgres:16}"
PG_CONTAINER_NAME="${PG_CONTAINER_NAME:-perle-qa-pg-${TIMESTAMP}}"
PG_HOST="${PG_HOST:-127.0.0.1}"
PG_PORT="${PG_PORT:-55432}"
PG_DB="${PG_DB:-perle_qa}"
PG_USER="${PG_USER:-perle_qa}"
PG_PASSWORD="${PG_PASSWORD:-perle_qa}"

SERVER_PID=""

cleanup() {
  set +e
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
  if [[ "$USE_DOCKER_POSTGRES" == "1" ]]; then
    docker rm -f "$PG_CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

if [[ "$USE_DOCKER_POSTGRES" == "1" ]]; then
  docker run -d \
    --name "$PG_CONTAINER_NAME" \
    -e POSTGRES_DB="$PG_DB" \
    -e POSTGRES_USER="$PG_USER" \
    -e POSTGRES_PASSWORD="$PG_PASSWORD" \
    -p "${PG_HOST}:${PG_PORT}:5432" \
    "$PG_IMAGE" >"$OUT_DIR/postgres_container_id.txt"

  ready="0"
  for _ in $(seq 1 60); do
    if docker exec "$PG_CONTAINER_NAME" pg_isready -U "$PG_USER" -d "$PG_DB" >/dev/null 2>&1; then
      ready="1"
      break
    fi
    sleep 1
  done
  if [[ "$ready" != "1" ]]; then
    echo "PostgreSQL no estuvo listo a tiempo." >&2
    exit 1
  fi

  export DATABASE_URL="postgresql://${PG_USER}:${PG_PASSWORD}@${PG_HOST}:${PG_PORT}/${PG_DB}?connect_timeout=5"
else
  : "${DATABASE_URL:?Debes exportar DATABASE_URL cuando USE_DOCKER_POSTGRES=0.}"
fi

export DEBUG=1
export DB_SSL_REQUIRE=0
export DB_CONN_MAX_AGE=0
export DJANGO_SECRET_KEY='qa-pg-stress-secret-key-with-more-than-fifty-chars-123456'
export ALLOWED_HOSTS="127.0.0.1,localhost,testserver"
export CSRF_TRUSTED_ORIGINS="http://127.0.0.1:${QA_PORT},http://localhost:${QA_PORT}"
export WHATSAPP_PHONE=""

"$PYTHON_BIN" manage.py migrate --noinput >"$OUT_DIR/migrate.log" 2>&1
"$PYTHON_BIN" manage.py seed_demo --reset >"$OUT_DIR/seed_demo.log" 2>&1

"$PYTHON_BIN" manage.py shell >"$OUT_DIR/setup_admin.log" 2>&1 <<PY
from django.contrib.auth import get_user_model
User = get_user_model()
user, _ = User.objects.get_or_create(
    username="${ADMIN_USER}",
    defaults={"email": "qa_admin@example.com", "is_staff": True, "is_superuser": True},
)
user.is_staff = True
user.is_superuser = True
user.set_password("${ADMIN_PASS}")
user.save()
print("qa_admin_ready", user.username)
PY

"$PYTHON_BIN" manage.py shell >"$OUT_DIR/seed_stock.log" 2>&1 <<PY
from apps.catalog.models import ProductVariant
from apps.inventory.models import StockLevel
variant = ProductVariant.objects.filter(is_active=True).order_by("id").first()
if variant is None:
    raise SystemExit("No active variant found.")
StockLevel.objects.update_or_create(variant=variant, defaults={"available": int("${STOCK_CAP}")})
print("variant_id", variant.id)
print("stock_cap", int("${STOCK_CAP}"))
PY

"$PYTHON_BIN" manage.py runserver "127.0.0.1:${QA_PORT}" --noreload >"$OUT_DIR/server.log" 2>&1 &
SERVER_PID="$!"

ready="0"
for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${QA_PORT}/api/products/" >/dev/null 2>&1; then
    ready="1"
    break
  fi
  sleep 1
done
if [[ "$ready" != "1" ]]; then
  echo "Django server no estuvo listo a tiempo." >&2
  tail -n 80 "$OUT_DIR/server.log" || true
  exit 1
fi

"$PYTHON_BIN" scripts/qa/stress_http.py \
  --base-url "http://127.0.0.1:${QA_PORT}" \
  --output-dir "$OUT_DIR" \
  --admin-user "$ADMIN_USER" \
  --admin-pass "$ADMIN_PASS" \
  --stock-cap "$STOCK_CAP" \
  >"$OUT_DIR/stress_stdout.log" 2>&1

"$PYTHON_BIN" scripts/qa/evaluate_stress.py \
  --input "$OUT_DIR/stress_all.json" \
  --stock-cap "$STOCK_CAP" \
  >"$OUT_DIR/evaluate.log" 2>&1

echo "$OUT_DIR" >"$ROOT_DIR/audit/pg_stress_latest.txt"
echo "QA stress PostgreSQL finalizado. Evidencia: $OUT_DIR"
