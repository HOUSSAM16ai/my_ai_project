#!/usr/bin/env bash
###############################################################################
# on-create.sh (Superhuman Automation v2)
#
# Executed only once when the container is created.
# Responsibilities:
#   1. Auto-generate .env from Codespaces secrets.
#   2. Install Python dependencies (to ensure sync with requirements.txt).
#   3. Run Database Migrations.
###############################################################################

set -Eeuo pipefail
source .devcontainer/utils.sh

trap 'err "An unexpected error occurred (Line $LINENO)."' ERR

log "🚀 On-Create: Initializing environment..."

# --- 1. .env Generation ---
log "Step 1/3: Checking for Codespaces secrets to generate .env..."

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
log "Step 2/3: Installing/Updating Python dependencies..."
# Although Dockerfile installs them, we run this to ensure any dev-time changes
# to requirements.txt are picked up immediately without rebuild.
pip install --no-cache-dir --upgrade pip
if [ -f requirements.txt ]; then
    pip install --no-cache-dir -r requirements.txt
fi
pip install --no-cache-dir ruff pytest
ok "✅ Dependencies installed."

# --- 3. Database Migrations ---
# Note: This assumes the DB service is reachable.
# In postCreateCommand, services defined in docker-compose might not be fully ready
# or reachable via localhost if we are inside one of them.
# However, we will attempt it. If it fails, on-start.sh will catch it.
log "Step 3/3: Attempting Database Migrations..."

# Wait for DB (simple check)
# We need to know the DB host. Usually 'db' or 'postgres'.
# Based on docker-compose.yml (implied), let's assume 'db' is the service name if it exists,
# or we rely on DATABASE_URL.
# Since we are IN the container, we might need to wait for the sidecar DB.
# For now, we'll skip heavy waiting here and let on-start handle it if this is too early,
# BUT the prompt explicitly asked for migrations here.
# We will try to run upgrade.
if command -v alembic &> /dev/null; then
    log "Running Alembic migrations..."
    # We use '|| true' to prevent failure if DB is not up yet (postCreate might happen before DB is ready)
    alembic upgrade head || warn "Migration attempt failed (DB might not be ready). Will retry in on-start.sh."
else
    warn "Alembic not found. Skipping migrations."
fi

ok "✅ On-Create script finished."
echo
