#!/usr/bin/env bash
###############################################################################
# on-create.sh (Superhuman Automation v2 - Optimized)
#
# Executed only once when the container is created.
# Responsibilities:
#   1. Auto-generate .env from Codespaces secrets.
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
      # Properly quote all values to handle spaces (e.g., ADMIN_NAME)
      echo "DATABASE_URL=\"${DATABASE_URL}\""
      echo "OPENROUTER_API_KEY=\"${OPENROUTER_API_KEY:-}\""
      echo "SECRET_KEY=\"${SECRET_KEY:-$(openssl rand -hex 32)}\""
      echo "ADMIN_EMAIL=\"${ADMIN_EMAIL:-benmerahhoussam16@gmail.com}\""
      echo "ADMIN_PASSWORD=\"${ADMIN_PASSWORD:-1111}\""
      echo "ADMIN_NAME=\"${ADMIN_NAME:-Houssam Benmerah}\""
      echo "SUPABASE_URL=\"${SUPABASE_URL:-}\""
      echo "SUPABASE_ANON_KEY=\"${SUPABASE_ANON_KEY:-}\""
      echo "SUPABASE_SERVICE_ROLE_KEY=\"${SUPABASE_SERVICE_ROLE_KEY:-}\""
    } > .env

    ok "✅ .env file automatically generated."
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
