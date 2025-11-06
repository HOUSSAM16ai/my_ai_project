#!/usr/bin/env bash
###############################################################################
# docker-quick-start.sh
#
# دليل سريع لبدء التطبيق باستخدام Docker Compose
# Quick guide to start the application using Docker Compose
#
# Usage:
#   ./docker-quick-start.sh           # Interactive setup
#   ./docker-quick-start.sh --auto    # Automatic setup
###############################################################################

set -Eeuo pipefail

# Colors for better readability
if [ -t 1 ]; then
  RED=$(printf '\033[31m'); GREEN=$(printf '\033[32m'); YELLOW=$(printf '\033[33m')
  CYAN=$(printf '\033[36m'); MAGENTA=$(printf '\033[35m'); BOLD=$(printf '\033[1m')
  RESET=$(printf '\033[0m')
else
  RED=""; GREEN=""; YELLOW=""; CYAN=""; MAGENTA=""; BOLD=""; RESET=""
fi

header()  { printf "\n%s%s═══════════════════════════════════════════════════%s\n" "$BOLD$MAGENTA" "$1" "$RESET"; }
step()    { printf "%s[خطوة %s]%s %s\n" "$CYAN" "$1" "$RESET" "$2"; }
success() { printf "%s[✓]%s %s\n" "$GREEN" "$RESET" "$1"; }
warn()    { printf "%s[⚠]%s %s\n" "$YELLOW" "$RESET" "$1"; }
error()   { printf "%s[✗]%s %s\n" "$RED" "$RESET" "$1" >&2; }
info()    { printf "   %s\n" "$1"; }
cmd()     { printf "%s> %s%s\n" "$BOLD$CYAN" "$1" "$RESET"; }

AUTO_MODE=false
if [ "${1:-}" = "--auto" ]; then
  AUTO_MODE=true
fi

clear
header "🐋 Docker Compose - دليل البدء السريع"
echo ""
echo "${BOLD}${CYAN}مرحبًا! هذا الدليل سيساعدك على تشغيل التطبيق بشكل صحيح${RESET}"
echo "Welcome! This guide will help you run the application correctly"
echo ""

# Detect docker-compose command (v1 or v2)
if command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker-compose"
elif docker compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker compose"
else
  error "Docker Compose غير مثبت / Docker Compose is not installed!"
  info "Install it from: https://docs.docker.com/compose/install/"
  exit 1
fi

# Check if Docker daemon is running
if ! docker ps >/dev/null 2>&1; then
  error "Docker غير مشغل / Docker daemon is not running!"
  info "Please start Docker and try again"
  exit 1
fi

success "Docker و Docker Compose جاهزان / Docker and Docker Compose are ready"
info "Using: $DOCKER_COMPOSE"
echo ""

# ============================================================================
# STEP 1: Check .env file
# ============================================================================
step "1" "فحص ملف .env / Checking .env file"
echo ""

if [ ! -f ".env" ]; then
  warn ".env غير موجود / .env file not found"
  
  if [ -f ".env.example" ]; then
    info "إنشاء .env من .env.example / Creating .env from .env.example"
    cp .env.example .env
    success "تم إنشاء .env / .env file created"
    echo ""
    
    warn "⚠️  مهم جداً / VERY IMPORTANT:"
    info "يجب عليك تعديل ملف .env وإضافة:"
    info "You must edit .env file and add:"
    echo ""
    info "  DATABASE_URL=postgresql://..."
    info "  OPENROUTER_API_KEY=sk-or-v1-..."
    info "  ADMIN_EMAIL=your-email@example.com"
    info "  ADMIN_PASSWORD=your-secure-password"
    echo ""
    
    if [ "$AUTO_MODE" = false ]; then
      read -p "اضغط Enter بعد تعديل .env / Press Enter after editing .env... "
    else
      warn "وضع تلقائي - يجب تعديل .env يدوياً / Auto mode - you must edit .env manually"
      sleep 2
    fi
  else
    error ".env.example غير موجود / .env.example not found!"
    exit 1
  fi
else
  success ".env موجود / .env file exists"
  
  # Quick validation
  if grep -q "^DATABASE_URL=" .env && grep -q "^OPENROUTER_API_KEY=" .env; then
    success "المتغيرات الأساسية موجودة / Basic variables found"
  else
    warn "تحقق من المتغيرات في .env / Check variables in .env"
  fi
fi

echo ""

# ============================================================================
# STEP 2: Build Docker images
# ============================================================================
step "2" "بناء صور Docker / Building Docker images"
echo ""
info "هذه الخطوة قد تستغرق بضع دقائق في المرة الأولى"
info "This step may take a few minutes the first time"
echo ""

cmd "$DOCKER_COMPOSE build"
if $DOCKER_COMPOSE build; then
  success "تم البناء بنجاح / Build successful"
else
  error "فشل البناء / Build failed"
  exit 1
fi

echo ""

# ============================================================================
# STEP 3: Run database migrations
# ============================================================================
step "3" "تشغيل ترحيلات قاعدة البيانات / Running database migrations"
echo ""
info "هذا سيقوم بإنشاء الجداول في قاعدة البيانات"
info "This will create database tables"
echo ""

cmd "$DOCKER_COMPOSE run --rm web flask db upgrade"
if $DOCKER_COMPOSE run --rm web flask db upgrade; then
  success "الترحيلات نجحت / Migrations successful"
else
  error "فشلت الترحيلات / Migrations failed"
  warn "تأكد من صحة DATABASE_URL في .env"
  warn "Make sure DATABASE_URL in .env is correct"
  exit 1
fi

echo ""

# ============================================================================
# STEP 4: Create admin user
# ============================================================================
step "4" "إنشاء مستخدم المشرف / Creating admin user"
echo ""
info "سيتم استخدام ADMIN_EMAIL و ADMIN_PASSWORD من .env"
info "Will use ADMIN_EMAIL and ADMIN_PASSWORD from .env"
echo ""

# Show both commands (they do the same thing)
info "${BOLD}الأوامر المتاحة / Available commands:${RESET}"
cmd "$DOCKER_COMPOSE run --rm web flask users create-admin"
cmd "$DOCKER_COMPOSE run --rm web flask users init-admin"
echo ""

if $DOCKER_COMPOSE run --rm web flask users create-admin; then
  success "تم إنشاء المشرف / Admin user created"
else
  warn "قد يكون المشرف موجوداً مسبقاً / Admin might already exist"
fi

echo ""

# ============================================================================
# STEP 5: Start services
# ============================================================================
step "5" "تشغيل الخدمات / Starting services"
echo ""

START_NOW="y"
if [ "$AUTO_MODE" = false ]; then
  read -p "هل تريد تشغيل الخدمات الآن؟ / Start services now? [Y/n]: " START_NOW
  START_NOW=${START_NOW:-y}
fi

if [[ "$START_NOW" =~ ^[Yy] ]]; then
  cmd "$DOCKER_COMPOSE up -d"
  if $DOCKER_COMPOSE up -d; then
    success "الخدمات تعمل الآن / Services are running"
    echo ""
    
    # Wait a moment for services to stabilize
    sleep 3
    
    # Show service status
    info "${BOLD}حالة الخدمات / Service status:${RESET}"
    $DOCKER_COMPOSE ps
    echo ""
    
    header "✅ التطبيق جاهز! / Application Ready!"
    echo ""
    
    info "${BOLD}الوصول إلى التطبيق / Access the application:${RESET}"
    info "🌐 http://localhost:5000"
    echo ""
    
    info "${BOLD}لوحة الإدارة / Admin Dashboard:${RESET}"
    info "📊 http://localhost:5000/admin/dashboard"
    echo ""
    
    info "${BOLD}بيانات الدخول / Login credentials:${RESET}"
    if grep -q "^ADMIN_EMAIL=" .env 2>/dev/null; then
      ADMIN_EMAIL=$(grep "^ADMIN_EMAIL=" .env | cut -d'=' -f2- | tr -d '"' | head -c 50)
      # Basic validation: check if it looks like an email
      if [[ "$ADMIN_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        info "📧 Email: ${ADMIN_EMAIL}"
      else
        info "📧 Email: (check your .env file - format may be invalid)"
      fi
    else
      info "📧 Email: (check your .env file)"
    fi
    info "🔑 Password: (check your .env file)"
    echo ""
    
    info "${BOLD}أوامر مفيدة / Useful commands:${RESET}"
    cmd "$DOCKER_COMPOSE logs -f              # عرض السجلات / View logs"
    cmd "$DOCKER_COMPOSE ps                   # حالة الخدمات / Service status"
    cmd "$DOCKER_COMPOSE stop                 # إيقاف الخدمات / Stop services"
    cmd "$DOCKER_COMPOSE restart              # إعادة تشغيل / Restart services"
    echo ""
    
    # Ask about logs
    if [ "$AUTO_MODE" = false ]; then
      read -p "عرض السجلات؟ / Show logs? [y/N]: " SHOW_LOGS
      SHOW_LOGS=${SHOW_LOGS:-n}
      
      if [[ "$SHOW_LOGS" =~ ^[Yy] ]]; then
        echo ""
        info "عرض السجلات المباشرة (Ctrl+C للخروج)"
        info "Showing live logs (Ctrl+C to exit)"
        sleep 1
        $DOCKER_COMPOSE logs -f
      fi
    fi
  else
    error "فشل تشغيل الخدمات / Failed to start services"
    exit 1
  fi
else
  info "يمكنك تشغيل الخدمات لاحقاً بالأمر:"
  info "You can start services later with:"
  cmd "$DOCKER_COMPOSE up -d"
fi

echo ""
header "🎉 انتهى! / Done!"
echo ""
