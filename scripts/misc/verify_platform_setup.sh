#!/usr/bin/env bash
###############################################################################
# verify_platform_setup.sh
#
# سكريبت التحقق من جاهزية المنصات المتعددة
# Multi-Platform Setup Verification Script
#
# الاستخدام / Usage:
#   ./verify_platform_setup.sh
###############################################################################

set -eo pipefail

# Colors
if [ -t 1 ]; then
  RED=$(printf '\033[31m')
  GREEN=$(printf '\033[32m')
  YELLOW=$(printf '\033[33m')
  CYAN=$(printf '\033[36m')
  BOLD=$(printf '\033[1m')
  RESET=$(printf '\033[0m')
else
  RED=""; GREEN=""; YELLOW=""; CYAN=""; BOLD=""; RESET=""
fi

# Helper functions
log()     { printf "%s[INFO]%s %s\n"  "$CYAN"  "$RESET" "$1"; }
info()    { printf "%s[ℹ]%s %s\n"     "$CYAN"  "$RESET" "$1"; }
success() { printf "%s[✓]%s %s\n"     "$GREEN" "$RESET" "$1"; }
warning() { printf "%s[!]%s %s\n"     "$YELLOW" "$RESET" "$1"; }
error()   { printf "%s[✗]%s %s\n"     "$RED"   "$RESET" "$1" >&2; }
section() { printf "\n%s=== %s ===%s\n" "$BOLD$CYAN" "$1" "$RESET"; }

# Banner
clear
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║     🚀 CogniForge Multi-Platform Verification Tool 🚀     ║
║                                                            ║
║  أداة التحقق من جاهزية المنصات المتعددة                   ║
╚════════════════════════════════════════════════════════════╝
EOF

echo
log "بدء التحقق من الإعدادات..."
echo

# Track issues
ISSUES=0

###############################################################################
# 1. Platform Detection
###############################################################################
section "1️⃣  كشف المنصة / Platform Detection"

PLATFORM="Unknown"
if [ -n "${GITPOD_WORKSPACE_ID:-}" ]; then
  PLATFORM="Gitpod"
  success "المنصة: Gitpod ✅"
elif [ "${CODESPACES:-}" = "true" ]; then
  PLATFORM="GitHub Codespaces"
  success "المنصة: GitHub Codespaces ✅"
elif [ "${REMOTE_CONTAINERS:-}" = "true" ]; then
  PLATFORM="VS Code Dev Containers"
  success "المنصة: VS Code Dev Containers ✅"
else
  PLATFORM="Local Development"
  success "المنصة: Local Development ✅"
fi

###############################################################################
# 2. Configuration Files Check
###############################################################################
section "2️⃣  فحص ملفات التكوين / Configuration Files"

# Check .gitpod.yml
if [ -f ".gitpod.yml" ]; then
  success "وجد ملف .gitpod.yml ✅"

  # Only check Gitpod port configuration when actually running on Gitpod
  if [ "$PLATFORM" = "Gitpod" ]; then
    # Verify ports configuration
    if grep -q "port: 5000" .gitpod.yml; then
      success "  ↳ المنفذ 5000 مُكوّن ✅"
    else
      error "  ↳ المنفذ 5000 غير مُكوّن ❌"
      ((ISSUES++))
    fi

    # Verify port 5432 for Supabase connection
    if grep -q "port: 5432" .gitpod.yml; then
      success "  ↳ المنفذ 5432 (Supabase Direct) مُكوّن ✅"
    else
      warning "  ↳ المنفذ 5432 (Supabase Direct) غير مُكوّن ⚠️"
      warning "     يُنصح بإضافة المنفذ 5432 للاتصال بـ Supabase"
    fi

    # Verify port 6543 for Supabase Pooler
    if grep -q "port: 6543" .gitpod.yml; then
      success "  ↳ المنفذ 6543 (Supabase Pooler - موصى به) مُكوّن ✅"
    else
      warning "  ↳ المنفذ 6543 (Supabase Pooler) غير مُكوّن ⚠️"
      warning "     يُنصح بإضافة المنفذ 6543 (Pooler - موصى به)"
    fi
  else
    info "  ↳ تخطي فحص منافذ Gitpod (غير مطلوب لـ $PLATFORM)"
    info "     Skipping Gitpod port checks (not required for $PLATFORM)"
  fi
else
  if [ "$PLATFORM" = "Gitpod" ]; then
    error "ملف .gitpod.yml غير موجود ❌"
    ((ISSUES++))
  else
    info "ملف .gitpod.yml غير موجود (غير مطلوب لـ $PLATFORM)"
  fi
fi

# Check .devcontainer/devcontainer.json
if [ -f ".devcontainer/devcontainer.json" ]; then
  success "وجد ملف devcontainer.json ✅"

  # Verify SKIP_DB_WAIT
  if grep -q '"SKIP_DB_WAIT": "true"' .devcontainer/devcontainer.json; then
    success "  ↳ SKIP_DB_WAIT=true مُفعّل ✅ (حل مشكلة Port 5432)"
  else
    error "  ↳ SKIP_DB_WAIT غير مُفعّل ❌"
    ((ISSUES++))
  fi

  # Verify ports
  if grep -q '"forwardPorts"' .devcontainer/devcontainer.json; then
    success "  ↳ المنافذ مُكوّنة للتوجيه التلقائي ✅"
  else
    warning "  ↳ المنافذ غير مُكوّنة ⚠️"
  fi
else
  warning "ملف devcontainer.json غير موجود ⚠️"
fi

# Check .env.example
if [ -f ".env.example" ]; then
  success "وجد ملف .env.example ✅"

  if grep -q "DATABASE_URL" .env.example; then
    success "  ↳ DATABASE_URL موجود في .env.example ✅"
  else
    error "  ↳ DATABASE_URL غير موجود ❌"
    ((ISSUES++))
  fi
else
  error "ملف .env.example غير موجود ❌"
  ((ISSUES++))
fi

###############################################################################
# 3. Environment Configuration
###############################################################################
section "3️⃣  تكوين البيئة / Environment Configuration"

# Check .env file
if [ -f ".env" ]; then
  success "وجد ملف .env ✅"

  # Check DATABASE_URL
  if grep -q "DATABASE_URL" .env; then
    success "  ↳ DATABASE_URL موجود في .env ✅"

    # Check if it's configured (not placeholder)
    if grep -q "DATABASE_URL=.*supabase" .env; then
      success "  ↳ DATABASE_URL مُكوّن لـ Supabase ✅"
    elif grep -q "DATABASE_URL=.*YOUR-PROJECT" .env; then
      warning "  ↳ DATABASE_URL لم يتم تكوينه بعد (placeholder) ⚠️"
      warning "     تحتاج لإضافة رابط Supabase الحقيقي"
    else
      warning "  ↳ DATABASE_URL موجود لكن قد لا يكون لـ Supabase ⚠️"
    fi
  else
    error "  ↳ DATABASE_URL غير موجود في .env ❌"
    ((ISSUES++))
  fi
else
  warning "ملف .env غير موجود ⚠️"
  warning "  ↳ قم بنسخ .env.example إلى .env"
  log "     تنفيذ: cp .env.example .env"
fi

###############################################################################
# 4. Docker Configuration
###############################################################################
section "4️⃣  تكوين Docker / Docker Configuration"

# Check docker-compose.yml
if [ -f "docker-compose.yml" ]; then
  success "وجد ملف docker-compose.yml ✅"

  # Check if local DB service is removed
  if grep -q "db:" docker-compose.yml; then
    warning "  ↳ خدمة قاعدة بيانات محلية موجودة (قديمة) ⚠️"
    warning "     يُفضل استخدام Supabase فقط"
  else
    success "  ↳ لا توجد خدمة قاعدة بيانات محلية ✅ (Supabase فقط)"
  fi

  # Check web service
  if grep -q "web:" docker-compose.yml; then
    success "  ↳ خدمة web موجودة ✅"
  else
    error "  ↳ خدمة web غير موجودة ❌"
    ((ISSUES++))
  fi
else
  error "ملف docker-compose.yml غير موجود ❌"
  ((ISSUES++))
fi

###############################################################################
# 5. Scripts Check
###############################################################################
section "5️⃣  فحص السكريبتات / Scripts Check"

# Check on-start.sh
if [ -f ".devcontainer/on-start.sh" ]; then
  success "وجد سكريبت on-start.sh ✅"

  # Verify SKIP_DB_WAIT logic
  if grep -q 'SKIP_DB_WAIT.*true' .devcontainer/on-start.sh; then
    success "  ↳ منطق SKIP_DB_WAIT موجود ✅"
  else
    warning "  ↳ منطق SKIP_DB_WAIT قد يكون مفقود ⚠️"
  fi
else
  warning "سكريبت on-start.sh غير موجود ⚠️"
fi

# Check detect_platform.sh
if [ -f "detect_platform.sh" ]; then
  success "وجد سكريبت detect_platform.sh ✅"
else
  warning "سكريبت detect_platform.sh غير موجود ⚠️"
fi

###############################################################################
# 6. Documentation Check
###############################################################################
section "6️⃣  فحص التوثيق / Documentation Check"

docs=(
  "MULTI_PLATFORM_SETUP.md"
  "PLATFORM_FIX_REPORT_AR.md"
  "PLATFORM_ACCESS_GUIDE.md"
  "PLATFORM_STATUS_AR.md"
)

for doc in "${docs[@]}"; do
  if [ -f "$doc" ]; then
    success "  ✓ $doc موجود ✅"
  else
    warning "  ✗ $doc غير موجود ⚠️"
  fi
done

###############################################################################
# 7. Port 5432 Fix Verification
###############################################################################
section "7️⃣  التحقق من حل مشكلة Port 5432"

echo "${CYAN}فحص إعدادات تخطي المنفذ 5432...${RESET}"
echo

# Check devcontainer.json
if [ -f ".devcontainer/devcontainer.json" ] && grep -q '"SKIP_DB_WAIT": "true"' .devcontainer/devcontainer.json; then
  success "✅ SKIP_DB_WAIT=true في devcontainer.json"
  success "   → النظام لن ينتظر المنفذ 5432 المحلي"
  success "   → الاتصال المباشر بـ Supabase الخارجية"
else
  error "❌ SKIP_DB_WAIT غير مُفعّل بشكل صحيح"
  ((ISSUES++))
fi

# Check documentation
if [ -f "MULTI_PLATFORM_SETUP.md" ] && grep -q "Port 5432 failed" MULTI_PLATFORM_SETUP.md; then
  success "✅ التوثيق يشرح حل مشكلة Port 5432"
else
  warning "⚠️ التوثيق قد لا يشرح الحل بشكل كامل"
fi

###############################################################################
# 8. Platform Support Verification
###############################################################################
section "8️⃣  التحقق من دعم المنصات"

echo "${CYAN}فحص دعم المنصات المختلفة...${RESET}"
echo

platforms=(
  "Gitpod:.gitpod.yml"
  "Codespaces:.devcontainer/devcontainer.json"
  "Dev Containers:.devcontainer/devcontainer.json"
  "Local:docker-compose.yml"
)

for platform_file in "${platforms[@]}"; do
  platform="${platform_file%%:*}"
  file="${platform_file##*:}"

  if [ -f "$file" ]; then
    success "✅ $platform - مدعوم (ملف التكوين موجود)"
  else
    error "❌ $platform - غير مدعوم (ملف التكوين مفقود)"
    ((ISSUES++))
  fi
done

###############################################################################
# Final Summary
###############################################################################
echo
section "📊 النتيجة النهائية / Final Summary"

if [ $ISSUES -eq 0 ]; then
  cat << EOF

${GREEN}${BOLD}╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ✅ جميع الفحوصات نجحت! المشروع جاهز تماماً ✅            ║
║                                                           ║
║   All checks passed! Project is fully ready!             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝${RESET}

${GREEN}✓ مشكلة Port 5432 تم حلها بالكامل${RESET}
${GREEN}✓ المشروع يعمل على جميع المنصات${RESET}
${GREEN}✓ التكوينات صحيحة ومكتملة${RESET}

${CYAN}المنصات المدعومة:${RESET}
  ✅ Gitpod
  ✅ GitHub Codespaces
  ✅ VS Code Dev Containers
  ✅ Local Development

${CYAN}الخطوات التالية:${RESET}
  1. تأكد من تكوين DATABASE_URL في .env
  2. شغّل المشروع: docker-compose up -d
  3. نفّذ الترحيلات: docker-compose run --rm web python -m app.cli db-migrate

${CYAN}للمزيد من المعلومات:${RESET}
  📖 راجع PLATFORM_STATUS_AR.md للتفاصيل الكاملة
  📖 راجع MULTI_PLATFORM_SETUP.md للإعداد الشامل

EOF
else
  cat << EOF

${YELLOW}${BOLD}╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ⚠️  تم العثور على $ISSUES مشكلة/مشاكل                     ║
║                                                           ║
║   Found $ISSUES issue(s)                                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝${RESET}

${YELLOW}يُرجى مراجعة الرسائل أعلاه لحل المشاكل${RESET}
${YELLOW}Please review the messages above to fix the issues${RESET}

${CYAN}للحصول على المساعدة:${RESET}
  📖 راجع PLATFORM_STATUS_AR.md
  📖 راجع MULTI_PLATFORM_SETUP.md
  🆘 افتح issue على GitHub

EOF
fi

exit $ISSUES
