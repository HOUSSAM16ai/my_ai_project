#!/usr/bin/env bash
###############################################################################
# on-start.sh
#
# يُنفَّذ عند بدء الحاوية (postStartCommand).
# المسؤوليات:
#   - انتظار قاعدة البيانات (ما لم يتم التخطي).
#   - تنفيذ الترحيلات (إن لم تُنفَّذ سابقًا + غير متخطاة).
#   - تنفيذ seeding (اختياري).
#   - تشغيل التطبيق (اختياري).
#
# متغيرات تحكم:
#   SKIP_DB_WAIT=true             -> لا تنتظر قاعدة البيانات
#   SKIP_MIGRATIONS=true          -> لا تنفذ الترحيلات
#   SKIP_SEED=true                -> لا تنفذ seeding
#   RUN_APP_ON_START=true         -> شغّل التطبيق تلقائيًا
#   APP_START_CMD="flask run ..." -> أمر التشغيل (افتراضي مقترح أدناه)
#   DB_HOST / DB_PORT / POSTGRES_USER / POSTGRES_DB
###############################################################################

set -Eeuo pipefail

if [ -t 1 ]; then
  RED=$(printf '\033[31m'); GREEN=$(printf '\033[32m'); YELLOW=$(printf '\033[33m')
  CYAN=$(printf '\033[36m'); BOLD=$(printf '\033[1m'); RESET=$(printf '\033[0m')
else
  RED=""; GREEN=""; YELLOW=""; CYAN=""; BOLD=""; RESET=""
fi

log()  { printf "%s[INFO]%s %s\n"  "$CYAN"  "$RESET" "$1"; }
ok()   { printf "%s[ OK ]%s %s\n"  "$GREEN" "$RESET" "$1"; }
warn() { printf "%s[WARN]%s %s\n"  "$YELLOW" "$RESET" "$1"; }
err()  { printf "%s[ERR ]%s %s\n"  "$RED"   "$RESET" "$1" >&2; }

trap 'err "حدث خطأ غير متوقع (Line $LINENO)."' ERR

cd /app || { err "لا يمكن الدخول إلى /app"; exit 1; }

echo
log "🚀 On-Start: Igniting the ecosystem..."

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

# (1) انتظار قاعدة البيانات
if [ "${SKIP_DB_WAIT:-false}" = "true" ]; then
  warn "تخطي انتظار قاعدة البيانات."
else
  log "انتظار PostgreSQL على $DB_HOST:$DB_PORT ..."
  if command -v pg_isready >/dev/null 2>&1; then
    ATTEMPTS=0; MAX=60
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
      ATTEMPTS=$((ATTEMPTS+1))
      if [ $ATTEMPTS -ge $MAX ]; then
        err "PostgreSQL لم يصبح جاهزًا بعد $(($MAX*2)) ثانية."
        exit 1
      fi
      echo "   - DB not ready yet..."
      sleep 2
    done
    ok "قاعدة البيانات جاهزة."
  else
    warn "pg_isready غير متوفر. استخدام اختبار TCP."
    until (echo > /dev/tcp/"$DB_HOST"/"$DB_PORT") >/dev/null 2>&1; do
      echo "   - Waiting for $DB_HOST:$DB_PORT ..."
      sleep 2
    done
    ok "المنفذ مفتوح."
  fi
fi

# (2) الترحيلات
if [ "${SKIP_MIGRATIONS:-false}" = "true" ]; then
  warn "تخطي الترحيلات."
else
  if command -v flask >/dev/null 2>&1; then
    log "تشغيل flask db upgrade ..."
    if FLASK_APP="${FLASK_APP:-app.py}" flask db upgrade; then
      ok "اكتملت الترحيلات."
    else
      warn "فشل flask db upgrade."
    fi
  else
    warn "flask غير متوفر."
  fi
fi

# (3) seeding
if [ "${SKIP_SEED:-false}" = "true" ]; then
  warn "تخطي seeding."
else
  if command -v flask >/dev/null 2>&1 && flask --help 2>&1 | grep -q "users"; then
    log "Seeding (flask users init-admin)..."
    if flask users init-admin; then
      ok "تم seeding (أو كان موجودًا)."
    else
      warn "فشل seeding."
    fi
  else
    warn "أمر seeding غير متوفر."
  fi
fi

# (4) تشغيل التطبيق (اختياري)
if [ "${RUN_APP_ON_START:-false}" = "true" ]; then
  APP_START_CMD="${APP_START_CMD:-flask run --host=0.0.0.0 --port=8000}"
  log "تشغيل التطبيق: $APP_START_CMD"
  # يُشغَّل في المقدمة (يمكن تحويله لخلفية حسب حاجتك)
  exec bash -lc "$APP_START_CMD"
else
  log "لن يتم تشغيل التطبيق تلقائيًا (اضبط RUN_APP_ON_START=true لتفعيله)."
fi

ok "انتهى on-start.sh."
echo