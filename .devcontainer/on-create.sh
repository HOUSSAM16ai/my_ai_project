#!/usr/bin/env bash
###############################################################################
# on-create.sh (Superhuman Automation v2)
#
# Executed only once when the container is created.
# Responsibilities:
#   1. Auto-generate .env from Codespaces secrets.
#   2. Install Python dependencies (to ensure sync with requirements.txt).
#   3. Run Smart Database Migrations (Idempotent).
#   4. Auto-seed Admin User.
###############################################################################

set -Eeuo pipefail
cd /app  # FORCE ROOT CONTEXT
source .devcontainer/utils.sh

trap 'err "An unexpected error occurred (Line $LINENO)."' ERR

log "🚀 On-Create: Initializing environment..."

# --- 1. .env Generation ---
log "Step 1/4: Checking for Codespaces secrets to generate .env..."

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
  ok ".env file check complete."
fi

# --- 2. Dependency Installation ---
log "Step 2/4: Installing/Updating Python dependencies..."
# Although Dockerfile installs them, we run this to ensure any dev-time changes
# to requirements.txt are picked up immediately without rebuild.
pip install --no-cache-dir --upgrade pip
if [ -f requirements.txt ]; then
    pip install --no-cache-dir -r requirements.txt
fi
pip install --no-cache-dir ruff pytest
ok "✅ Dependencies installed."

# --- 3. Smart Database Migrations ---
# Note: This uses the smart_migrate script to handle existing DBs safely.
log "Step 3/4: Attempting Smart Database Migrations..."

if [ -f "scripts/smart_migrate.py" ]; then
    log "Running Smart Migration Strategy..."
    python scripts/smart_migrate.py || warn "Migration attempt failed (DB might not be ready). Will retry in on-start.sh."
else
    warn "scripts/smart_migrate.py not found. Skipping migrations."
fi

# --- 4. Admin Seeding ---
log "Step 4/4: Auto-seeding Admin User..."
if [ -f "scripts/seed_admin.py" ]; then
    python scripts/seed_admin.py || warn "Admin seeding failed (DB might not be ready). Will retry in on-start.sh."
else
    warn "scripts/seed_admin.py not found. Skipping admin seeding."
fi

ok "✅ On-Create script finished."
echo
