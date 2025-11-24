#!/usr/bin/env bash
###############################################################################
# launch_stack.sh (Superhuman Supervisor)
#
# This script orchestrates the entire application startup sequence in the background.
# It is designed to be called by .devcontainer/on-start.sh to allow the lifecycle
# hook to return immediately, preventing Codespaces from hanging.
#
# Responsibilities:
#   1. Wait for Database availability.
#   2. Run Smart Migrations.
#   3. Seed Admin User.
#   4. Launch Uvicorn Server.
###############################################################################

set -Eeuo pipefail

# Define log file
LOG_FILE=".superhuman_bootstrap.log"

# Function to log to file and stdout (if available)
log() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [INFO] $1" >> "$LOG_FILE"
}

warn() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [WARN] $1" >> "$LOG_FILE"
}

err() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [ERR ] $1" >> "$LOG_FILE"
}

# --- Initialize ---
log "🚀 Superhuman Supervisor: Boot sequence initiated."
cd /app || { err "Failed to cd to /app"; exit 1; }

# Source environment
if [ -f .env ]; then
    log "Loading .env file..."
    set -a
    source .env
    set +a
fi

# --- Step 1: Dependencies ---
log "Step 1/4: Checking dependencies..."
if pip install --no-cache-dir -r requirements.txt >> "$LOG_FILE" 2>&1; then
    log "✅ Dependencies verified."
else
    warn "Dependency check had issues. See logs."
fi

# --- Step 2: Migrations ---
log "Step 2/4: Smart Migrations..."
if [ -f "scripts/smart_migrate.py" ]; then
    log "Executing smart_migrate.py..."
    if python scripts/smart_migrate.py >> "$LOG_FILE" 2>&1; then
        log "✅ Migrations completed successfully."
    else
        err "❌ Migrations failed. Application may not behave correctly."
        # We continue anyway to try and start the app, so user can debug.
    fi
else
    warn "scripts/smart_migrate.py not found."
fi

# --- Step 3: Admin Seeding ---
log "Step 3/4: Admin Seeding..."
if [ -f "scripts/seed_admin.py" ]; then
    if python scripts/seed_admin.py >> "$LOG_FILE" 2>&1; then
        log "✅ Admin seeded."
    else
        warn "❌ Admin seeding failed."
    fi
fi

# --- Step 4: Launch App ---
log "Step 4/4: Launching Uvicorn..."

# Check if already running
if pgrep -f "uvicorn" > /dev/null; then
    log "✅ Application is already running."
else
    # We execute start.sh directly here.
    # Note: We don't need nohup here because this whole script is already nohup'd by on-start.sh
    # But scripts/start.sh uses 'exec', so it will replace this shell.
    log "🚀 Executing scripts/start.sh..."

    # We redirect output of the app to a separate log or append to this one?
    # Let's append to a dedicated app log for clarity, or keep it unified.
    # Standard practice: app logs to stdout/stderr.
    # Since this script is running in background with output redirected to LOG_FILE (by on-start.sh),
    # executing start.sh will inherit that redirection if we don't change it.

    # However, scripts/start.sh does: exec python ...
    # on-start.sh does: nohup bash scripts/launch_stack.sh > .superhuman_bootstrap.log 2>&1 &

    # So uvicorn output will go to .superhuman_bootstrap.log. This is good.
    bash scripts/start.sh >> "$LOG_FILE" 2>&1 &
    PID=$!
    log "✅ Uvicorn started with PID $PID. Logs are streaming to $LOG_FILE"
fi

log "🎉 --- Supervisor sequence complete --- 🎉"
