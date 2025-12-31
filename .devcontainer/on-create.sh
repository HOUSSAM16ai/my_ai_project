#!/usr/bin/env bash
###############################################################################
# on-create.sh - DevContainer Post-Create Hook (v2.0)
#
# يُنفَّذ مرة واحدة فقط عند إنشاء الحاوية
# Executed only once when the container is created
#
# المسؤوليات (Responsibilities):
#   1. توليد ملف .env من أسرار Codespaces
#   2. التحقق من صحة التكوين
#   3. تهيئة مجلدات الحالة
#
# المبادئ (Principles):
#   - Fast Path: < 5 seconds execution time
#   - Idempotent: Safe to run multiple times
#   - Secrets Only: No heavy operations
#   - Fail Fast: Exit on any error
#
# الإصدار (Version): 2.0.0
# التاريخ (Date): 2025-12-31
###############################################################################

set -Eeuo pipefail

# ==============================================================================
# INITIALIZATION (التهيئة)
# ==============================================================================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly APP_ROOT="/app"

cd "$APP_ROOT"

# Load core library
if [ -f "$SCRIPT_DIR/lib/lifecycle_core.sh" ]; then
    source "$SCRIPT_DIR/lib/lifecycle_core.sh"
else
    echo "ERROR: lifecycle_core.sh not found" >&2
    exit 1
fi

# Error trap
trap 'lifecycle_error "Unexpected error at line $LINENO"' ERR

lifecycle_info "═══════════════════════════════════════════════════════"
lifecycle_info "🚀 Post-Create Hook: Environment Configuration"
lifecycle_info "═══════════════════════════════════════════════════════"

# ==============================================================================
# STEP 1: Environment File Generation (توليد ملف البيئة)
# ==============================================================================

lifecycle_info "Step 1/3: Environment file generation..."

generate_env_file() {
    lifecycle_info "Generating .env from Codespaces secrets..."
    
    cat > .env <<EOF
# ══════════════════════════════════════════════════════════════════════
# CogniForge Environment Configuration
# Auto-generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
# ══════════════════════════════════════════════════════════════════════

# 🔐 CORE SECRETS | الأسرار الأساسية
DATABASE_URL="${DATABASE_URL}"
SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}"
OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"

# 👤 ADMIN CONFIGURATION | تكوين المسؤول
ADMIN_EMAIL="${ADMIN_EMAIL:-benmerahhoussam16@gmail.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-1111}"
ADMIN_NAME="${ADMIN_NAME:-Houssam Benmerah}"

# 🗄️ SUPABASE CONFIGURATION | تكوين Supabase
SUPABASE_URL="${SUPABASE_URL:-}"
SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY:-}"
SUPABASE_SERVICE_ROLE_KEY="${SUPABASE_SERVICE_ROLE_KEY:-}"

# ⚙️ APPLICATION SETTINGS | إعدادات التطبيق
ENVIRONMENT="${ENVIRONMENT:-development}"
TESTING="${TESTING:-0}"

# ══════════════════════════════════════════════════════════════════════
# ⚠️ NOTE: AI Models are configured in app/config/ai_models.py
# ══════════════════════════════════════════════════════════════════════
EOF
    
    lifecycle_info "✅ .env file generated successfully"
}

if [ ! -f ".env" ]; then
    if [ -n "${CODESPACES:-}" ] && [ -n "${DATABASE_URL:-}" ]; then
        generate_env_file
        lifecycle_set_state "env_generated" "codespaces"
    else
        lifecycle_warn "Not in Codespaces or DATABASE_URL not set"
        if [ -f ".env.example" ]; then
            cp .env.example .env
            lifecycle_info "Copied .env.example to .env"
            lifecycle_set_state "env_generated" "example"
        else
            lifecycle_error ".env.example not found"
            exit 1
        fi
    fi
else
    lifecycle_info ".env file already exists (skipping generation)"
fi

# ==============================================================================
# STEP 2: Configuration Validation (التحقق من التكوين)
# ==============================================================================

lifecycle_info "Step 2/3: Configuration validation..."

validate_env_file() {
    local required_vars=("DATABASE_URL" "SECRET_KEY")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env 2>/dev/null; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        lifecycle_error "Missing required variables: ${missing_vars[*]}"
        return 1
    fi
    
    lifecycle_info "✅ Configuration validated"
    return 0
}

if validate_env_file; then
    lifecycle_set_state "config_validated" "success"
else
    lifecycle_error "Configuration validation failed"
    exit 1
fi

# ==============================================================================
# STEP 3: State Initialization (تهيئة الحالة)
# ==============================================================================

lifecycle_info "Step 3/3: State initialization..."

# Create necessary directories
mkdir -p .devcontainer/state .devcontainer/locks
lifecycle_info "State directories created"

# Mark creation complete
lifecycle_set_state "container_created" "$(date +%s)"
lifecycle_info "✅ Container creation state recorded"

# ==============================================================================
# COMPLETION (الإكمال)
# ==============================================================================

lifecycle_info "═══════════════════════════════════════════════════════"
lifecycle_info "✅ Post-Create Hook Completed Successfully"
lifecycle_info "   Duration: Fast Path (< 5s)"
lifecycle_info "   Next: postStartCommand will launch services"
lifecycle_info "═══════════════════════════════════════════════════════"

exit 0
