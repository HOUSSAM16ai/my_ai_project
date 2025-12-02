#!/usr/bin/env bash
###############################################################################
# on-create.sh (Superhuman Automation v4 - Secrets Only)
#
# Executed only once when the container is created.
# Responsibilities:
#   1. Auto-generate .env from Codespaces secrets (SECRETS ONLY).
#
# ⚠️ IMPORTANT: AI Models are NOT configured here!
#    AI Models are configured in: app/config/ai_models.py → class ActiveModels
#    This script only handles SECRETS (API keys, Database URLs, etc.)
#
# Note: Heavy operations (pip install, migrations, seeding) have been moved
# to on-start.sh to prevent 'Freezing' during the Create phase.
###############################################################################

set -Eeuo pipefail
cd /app  # FORCE ROOT CONTEXT
source .devcontainer/utils.sh

trap 'err "An unexpected error occurred (Line $LINENO)."' ERR

log "🚀 On-Create: Initializing environment..."

# --- 1. .env Generation ---
log "Step 1/1: Checking for Codespaces secrets to generate .env..."

if [ ! -f ".env" ] && [ -n "${CODESPACES:-}" ]; then
  if [ -n "${DATABASE_URL:-}" ]; then
    ok "Found DATABASE_URL secret. Generating .env file automatically..."

    {
      # ══════════════════════════════════════════════════════════════════════
      # 🔐 CORE SECRETS ONLY | الأسرار الأساسية فقط
      # ══════════════════════════════════════════════════════════════════════
      # ⚠️ NOTE: AI Models are NOT secrets - they are configured in:
      #    app/config/ai_models.py → class ActiveModels
      # ══════════════════════════════════════════════════════════════════════
      echo "# Core Secrets (Auto-generated from Codespaces Secrets)"
      echo "DATABASE_URL=\"${DATABASE_URL}\""
      echo "SECRET_KEY=\"${SECRET_KEY:-$(openssl rand -hex 32)}\""
      echo "OPENROUTER_API_KEY=\"${OPENROUTER_API_KEY:-}\""
      
      # ══════════════════════════════════════════════════════════════════════
      # 👤 ADMIN CONFIGURATION | تكوين المسؤول
      # ══════════════════════════════════════════════════════════════════════
      echo ""
      echo "# Admin Configuration"
      echo "ADMIN_EMAIL=\"${ADMIN_EMAIL:-benmerahhoussam16@gmail.com}\""
      echo "ADMIN_PASSWORD=\"${ADMIN_PASSWORD:-1111}\""
      echo "ADMIN_NAME=\"${ADMIN_NAME:-Houssam Benmerah}\""
      
      # ══════════════════════════════════════════════════════════════════════
      # 🗄️ SUPABASE CONFIGURATION | تكوين Supabase
      # ══════════════════════════════════════════════════════════════════════
      echo ""
      echo "# Supabase Configuration"
      echo "SUPABASE_URL=\"${SUPABASE_URL:-}\""
      echo "SUPABASE_ANON_KEY=\"${SUPABASE_ANON_KEY:-}\""
      echo "SUPABASE_SERVICE_ROLE_KEY=\"${SUPABASE_SERVICE_ROLE_KEY:-}\""
      
    } > .env

    ok "✅ .env file automatically generated (Secrets only - AI models are in app/config/ai_models.py)."
  else
    warn "DATABASE_URL secret not found. Manual .env setup will be required."
    # Copy example file so the user has a template
    [ ! -f ".env" ] && cp .env.example .env
  fi
else
  ok ".env file check complete."
fi

ok "✅ On-Create script finished (Fast Path)."
echo
