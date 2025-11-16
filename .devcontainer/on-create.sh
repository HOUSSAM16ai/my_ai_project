#!/usr/bin/env bash
###############################################################################
# on-create.sh (Superhuman Automation v2)
#
# Executed only once when the container is created.
# Responsibilities:
#   1. Auto-generate .env from Codespaces secrets.
#   2. Build all Docker services.
###############################################################################

set -Eeuo pipefail
source .devcontainer/utils.sh

trap 'err "An unexpected error occurred (Line $LINENO)."' ERR

log "🚀 On-Create: Initializing environment..."

# --- SUPERHUMAN: Auto-configure from Codespaces Secrets ---
log "Step 1/2: Checking for Codespaces secrets to generate .env..."

if [ ! -f ".env" ] && [ -n "${CODESPACES:-}" ]; then
  if [ -n "${DATABASE_URL:-}" ]; then
    ok "Found DATABASE_URL secret. Generating .env file automatically..."

    {
      echo "DATABASE_URL=${DATABASE_URL}"
      echo "OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-}"
      echo "SECRET_KEY=${SECRET_KEY:-$(openssl rand -hex 32)}"
      echo "ADMIN_EMAIL=${ADMIN_EMAIL:-benmerahhoussam16@gmail.com}"
      echo "ADMIN_PASSWORD=${ADMIN_PASSWORD:-1111}"
      echo "ADMIN_NAME=${ADMIN_NAME:-'Houssam Benmerah'}"
      echo "SUPABASE_URL=${SUPABASE_URL:-}"
      echo "SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY:-}"
      echo "SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY:-}"
    } > .env

    ok "✅ .env file automatically generated."
  else
    warn "DATABASE_URL secret not found. Manual .env setup will be required."
    # Copy example file so the user has a template
    [ ! -f ".env" ] && cp .env.example .env
  fi
else
  ok ".env file already exists or not in Codespaces. Skipping generation."
fi

log "Step 2/2: Building Docker images..."
docker-compose build

ok "✅ On-Create script finished. Environment is ready."
echo
