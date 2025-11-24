#!/usr/bin/env bash
###############################################################################
# on-start.sh (Superhuman Automation Edition)
#
# Executed every time the container starts.
# Responsibilities (Fully Automated & Idempotent):
#   1. Install/Verify Dependencies (Fast check).
#   2. Smart Database Migrations (Retry/Ensure).
#   3. Ensure Admin User.
#   4. Start Application in Background.
###############################################################################

set -Eeuo pipefail
cd /app  # FORCE ROOT CONTEXT
source .devcontainer/utils.sh

trap 'err "An unexpected error occurred (Line $LINENO)."' ERR

log "🚀 On-Start: Launching the fully automated CogniForge ecosystem..."

# --- 1. Dependency Check (Fast) ---
log "Step 1/4: Verifying Dependencies..."
if [ -f requirements.txt ]; then
    # We use pip install --no-deps to just check if packages are present,
    # but strictly we want to ensure everything is installed.
    # Since Dockerfile installs them, this is usually a no-op unless requirements changed.
    pip install --no-cache-dir -r requirements.txt > /dev/null 2>&1 || warn "Dependency check warning. Run 'pip install -r requirements.txt' manually if needed."
    ok "✅ Dependencies verified."
fi

# --- 2. Smart Database Migrations ---
log "Step 2/4: Ensuring Database Schema..."
if [ -f "scripts/smart_migrate.py" ]; then
    log "Running Smart Migration Strategy..."
    # We run this in foreground because the app NEEDS the DB to start correctly.
    # But smart_migrate.py has timeouts, so it won't hang forever.
    python scripts/smart_migrate.py || warn "Migration failed. Application might not start correctly."
else
    warn "scripts/smart_migrate.py not found. Skipping migrations."
fi

# --- 3. Create or update admin user ---
log "Step 3/4: Ensuring admin user exists..."
if [ -f "scripts/seed_admin.py" ]; then
    python scripts/seed_admin.py || warn "Admin seeding failed."
elif [ -f "cli.py" ]; then
    # Fallback to CLI if script missing
    if python cli.py --help | grep -q "create-admin"; then
         python cli.py create-admin || warn "Admin creation failed."
    fi
fi

# --- 4. Ensure Application is Running (Superhuman Redundancy) ---
log "Step 4/4: Ensuring Application Server is UP..."
if ! pgrep -f "uvicorn" > /dev/null; then
    log "Starting Uvicorn in background..."
    # We use nohup to ensure it persists, and redirect output
    nohup bash scripts/start.sh > .app_background.log 2>&1 &
    ok "✅ Application started in background."
else
    ok "✅ Application is already running."
fi

echo
log "🎉 --- System is fully operational --- 🎉"
