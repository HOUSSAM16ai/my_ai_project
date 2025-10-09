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

# تحميل .env بطريقة آمنة - فقط إذا لم تكن Secrets موجودة
load_env_file_if_needed() {
  # إذا secrets موجودة، لا تحمّل .env
  if [[ -n "${DATABASE_URL:-}" && -n "${OPENROUTER_API_KEY:-}" ]]; then
    log "🔐 استخدام Codespaces Secrets (DATABASE_URL و OPENROUTER_API_KEY موجودة)"
    return 0
  fi

  local env_file="${1:-.env}"
  [[ ! -f "$env_file" ]] && return 0

  log "📄 تحميل المتغيرات من $env_file"

  while IFS= read -r line || [[ -n "$line" ]]; do
    # إزالة المسافات في الأطراف
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    # تجاهل الفارغ والتعليقات
    [[ -z "$line" || "${line:0:1}" == "#" ]] && continue
    # تخطي الأسطر غير المطابقة للشكل KEY=VALUE
    [[ "$line" != *"="* ]] && continue

    local key="${line%%=*}"
    local val="${line#*=}"

    # تنظيف المفتاح من المسافات
    key="$(echo -n "$key" | sed -E 's/[[:space:]]+//g')"
    # التحقق من صلاحية اسم المتغير
    if ! [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
      continue
    fi

    # إزالة التعليقات الداخلية إن كانت القيمة غير محاطة باقتباس
    if [[ "$val" != \"*\" && "$val" != \'*\' ]]; then
      val="${val%%#*}"
      val="${val%"${val##*[![:space:]]}"}"
    fi

    # لا تطغى على المتغير إن كان قادماً من Secrets
    if [[ -z "${!key:-}" ]]; then
      export "$key=$val"
    fi
  done < "$env_file"
}

load_env_file_if_needed ".env" || true

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
    # جرّب المضيف من DATABASE_URL إن أمكن
    if [[ -n "${DATABASE_URL:-}" ]]; then
      host="$(python3 - <<'PY'
import os,sys,urllib.parse
u=os.environ.get("DATABASE_URL","")
try:
    p=urllib.parse.urlparse(u)
    print(p.hostname or "")
except Exception:
    print("")
PY
)"
      port="$(python3 - <<'PY'
import os,sys,urllib.parse
u=os.environ.get("DATABASE_URL","")
try:
    p=urllib.parse.urlparse(u)
    print(p.port or 5432)
except Exception:
    print(5432)
PY
)"
      pg_isready -h "${host:-localhost}" -p "${port:-5432}" || warn "PostgreSQL غير جاهز حالياً."
    else
      if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
        ok "PostgreSQL جاهز."
      else
        warn "PostgreSQL غير جاهز حالياً."
      fi
    fi
  else
    warn "pg_isready غير متوفر — تخطي الفحص."
  fi
fi

# حالة الترحيلات
if [ "${SHOW_MIGRATION_STATUS:-true}" = "true" ]; then
  log "فحص حالة الترحيلات..."
  if command -v flask >/dev/null 2>&1; then
    export FLASK_APP="${FLASK_APP:-run:app}"
    if python3 -c "import flask_migrate" >/dev/null 2>&1; then
      flask db current || warn "تعذر الحصول على حالة الترحيلات."
    else
      warn "Flask-Migrate غير مثبت."
    fi
  else
    warn "flask غير متاح."
  fi
else
  warn "تخطي عرض حالة الترحيلات (SHOW_MIGRATION_STATUS=false)."
fi

echo
ok "📌 جاهز للعمل. يمكنك تشغيل التطبيق بأمر مثل:"
echo "   flask run --host=0.0.0.0 --port=8000"
echo "   أو: docker-compose up --build"
echo