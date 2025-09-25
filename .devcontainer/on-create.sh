#!/usr/bin/env bash
###############################################################################
# on-create.sh
#
# يُنفَّذ بعد إنشاء الحاوية مباشرة (postCreateCommand).
# المسؤوليات:
#   1. إنشاء ملف .env إن لم يكن موجوداً (من .env.example).
#   2. تثبيت متطلبات بايثون (مرة واحدة فقط).
#   3. (اختياري) تنفيذ الترحيلات + seeding إن تم تفعيلها هنا.
#
# قابلية التحكم عبر متغيرات بيئة (يمكن ضبطها في devcontainer.json أو .env):
#   SKIP_ENV_BOOTSTRAP=true      -> تخطي إنشاء .env
#   SKIP_PIP_INSTALL=true        -> تخطي تثبيت الحزم
#   SKIP_MIGRATIONS=true         -> عدم تنفيذ flask db upgrade
#   SKIP_SEED=true               -> عدم تنفيذ seeding
#   RUN_MIGRATIONS_DURING_CREATE=true  -> نفّذ الترحيلات في هذه المرحلة
#   RUN_SEED_DURING_CREATE=true        -> نفّذ seeding في هذه المرحلة
#
# ملاحظات:
#  - لا نستخدم docker-compose داخل الحاوية.
#  - أي تشغيل للتطبيق يفضّل نقله إلى on-start.sh.
###############################################################################

set -Eeuo pipefail

# ألوان
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

PROJECT_ROOT="/app"
cd "$PROJECT_ROOT" || { err "لا يمكن الدخول إلى $PROJECT_ROOT"; exit 1; }

echo
log "✅ On-Create: Bootstrapping foundational layers..."

# (1) إنشاء .env إن لم يوجد
if [ "${SKIP_ENV_BOOTSTRAP:-false}" = "true" ]; then
  warn "تخطي إنشاء ملف .env (SKIP_ENV_BOOTSTRAP=true)"
else
  if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
      cp .env.example .env
      ok "تم إنشاء .env من .env.example"
    else
      warn "لا يوجد .env ولا .env.example — أنشئ .env يدويًا لاحقًا."
    fi
  else
    log ".env موجود مسبقًا — لن يتم استبداله."
  fi
fi

# (2) تثبيت الحزم (مرّة أولى فقط)
SENTINEL=".devcontainer/.pip_installed"
if [ "${SKIP_PIP_INSTALL:-false}" = "true" ]; then
  warn "تخطي pip install (SKIP_PIP_INSTALL=true)"
else
  if [ -f "$SENTINEL" ]; then
    log "الحزم مثبتة سابقًا (مؤشر $SENTINEL موجود)."
  else
    if [ -f "requirements.txt" ]; then
      log "تثبيت اعتماديات بايثون..."
      pip install --no-cache-dir -r requirements.txt
      mkdir -p "$(dirname "$SENTINEL")"
      touch "$SENTINEL"
      ok "تم تثبيت الحزم."
    else
      warn "لا يوجد requirements.txt — تخطي التثبيت."
    fi
  fi
fi

# (3) تحميل متغيرات من .env (اختياري)
if [ -f ".env" ]; then
  # shellcheck disable=SC2046
  export $(grep -E '^[A-Za-z0-9_]+=' .env | sed 's/\r$//') || true
fi

# (4) الترحيلات أثناء on-create (اختياري)
if [ "${RUN_MIGRATIONS_DURING_CREATE:-false}" = "true" ] && [ "${SKIP_MIGRATIONS:-false}" != "true" ]; then
  if command -v flask >/dev/null 2>&1; then
    log "تنفيذ الترحيلات الآن (on-create)..."
    if FLASK_APP="${FLASK_APP:-app.py}" flask db upgrade; then
      ok "اكتملت الترحيلات."
    else
      warn "فشل flask db upgrade (تحقق من FLASK_APP)."
    fi
  else
    warn "أمر flask غير متوفر."
  fi
else
  log "لن ننفذ الترحيلات الآن (يمكن تنفيذها لاحقًا في on-start)."
fi

# (5) seeding أثناء on-create (اختياري)
if [ "${RUN_SEED_DURING_CREATE:-false}" = "true" ] && [ "${SKIP_SEED:-false}" != "true" ]; then
  if command -v flask >/dev/null 2>&1 && flask --help 2>&1 | grep -q "users"; then
    log "تشغيل seeding (init-admin)..."
    if flask users init-admin; then
      ok "اكتمل seeding."
    else
      warn "فشل seeding."
    fi
  else
    warn "flask أو أمر users غير متوفر."
  fi
else
  log "لن ننفذ seeding الآن."
fi

ok "انتهى on-create.sh. جاهز للخطوة التالية."
echo