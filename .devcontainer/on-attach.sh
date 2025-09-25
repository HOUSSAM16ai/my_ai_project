#!/usr/bin/env bash
###############################################################################
# on-attach.sh
#
# يُنفَّذ عند إرفاق محرر (postAttachCommand).
# الهدف:
#   - عرض حالة سريعة للبيئة.
#   - فحص جاهزية قاعدة البيانات (اختياري).
#   - استعراض نسخة الترحيل الحالية (إن وُجدت Alembic/Flask-Migrate).
#   - عدم تنفيذ عمليات ثقيلة.
#
# متغيرات:
#   SKIP_ATTACH_DB_CHECK=true    -> عدم فحص قاعدة البيانات
#   SHOW_MIGRATION_STATUS=true   -> عرض حالة الترحيلات
###############################################################################

set -Eeuo pipefail

if [ -t 1 ]; then
  RED=$(printf '\033[31m'); GREEN=$(printf '\033[32m'); YELLOW=$(printf '\033[33m')
  CYAN=$(printf '\033[36m'); MAGENTA=$(printf '\033[35m'); RESET=$(printf '\033[0m')
else
  RED=""; GREEN=""; YELLOW=""; CYAN=""; MAGENTA=""; RESET=""
fi

section() { printf "\n%s========== %s ==========%s\n" "$MAGENTA" "$1" "$RESET"; }
log()     { printf "%s[INFO]%s %s\n" "$CYAN" "$RESET" "$1"; }
ok()      { printf "%s[ OK ]%s %s\n" "$GREEN" "$RESET" "$1"; }
warn()    { printf "%s[WARN]%s %s\n" "$YELLOW" "$RESET" "$1"; }
err()     { printf "%s[ERR ]%s %s\n" "$RED" "$RESET" "$1" >&2; }

trap 'err "حدث خطأ غير متوقع (Line $LINENO)."' ERR

cd /app || { err "لا يمكن الدخول إلى /app"; exit 1; }

echo
section "On-Attach: Runtime Snapshot"

# تحميل .env
if [ -f ".env" ]; then
  # shellcheck disable=SC2046
  export $(grep -E '^[A-Za-z0-9_]+=' .env | sed 's/\r$//') || true
fi

DB_HOST="${DB_HOST:-${POSTGRES_HOST:-db}}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${POSTGRES_USER:-user}"
DB_NAME="${POSTGRES_DB:-mydb}"

log "معلومات أساسية:"
echo "  - المسار الحالي: $(pwd)"
echo "  - Python: $(python --version 2>/dev/null || echo 'N/A')"
echo "  - حزم مثبّتة: $(pip list 2>/dev/null | wc -l | awk '{print $1}') (عدد الأسطر في pip list)"

# فحص قاعدة البيانات
if [ "${SKIP_ATTACH_DB_CHECK:-false}" = "true" ]; then
  warn "تخطي فحص جاهزية قاعدة البيانات."
else
  log "فحص جاهزية قاعدة البيانات (سريع)..."
  if command -v pg_isready >/dev/null 2>&1; then
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
      ok "PostgreSQL جاهز."
    else
      warn "PostgreSQL غير جاهز حالياً."
    fi
  else
    warn "pg_isready غير متوفر — تخطي الفحص."
  fi
fi

# حالة الترحيلات
if [ "${SHOW_MIGRATION_STATUS:-true}" = "true" ]; then
  log "فحص حالة الترحيلات..."
  if command -v flask >/dev/null 2>&1 && flask --help 2>&1 | grep -q "db"; then
    if FLASK_APP="${FLASK_APP:-app.py}" flask db current 2>/dev/null; then
      ok "تم استرجاع حالة الترحيلات."
    else
      warn "تعذر استرجاع حالة الترحيلات (تحقق من FLASK_APP)."
    fi
  else
    warn "flask db غير متاح."
  fi
else
  warn "تخطي عرض حالة الترحيلات (SHOW_MIGRATION_STATUS=false)."
fi

echo
ok "📌 جاهز للعمل. يمكنك تشغيل التطبيق بأمر مثل:"
echo "   flask run --host=0.0.0.0 --port=8000"
echo "   أو: docker-compose up --build"
echo