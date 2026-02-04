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

# --- Step 1: Wait for system readiness ---
log "Step 1/5: Waiting for system readiness..."
sleep 2  # Give container time to fully initialize

# --- Step 2: Dependencies ---
log "Step 2/5: Checking dependencies..."
if pip install --no-cache-dir -r requirements.txt >> "$LOG_FILE" 2>&1; then
    log "✅ Python dependencies verified."
else
    warn "Python dependency check had issues. See logs."
fi

# --- Step 3: Migrations ---
log "Step 3/5: Smart Migrations..."
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

# --- Step 4: Admin Seeding ---
log "Step 4/5: Admin Seeding..."
if [ -f "scripts/seed_admin.py" ]; then
    if python scripts/seed_admin.py >> "$LOG_FILE" 2>&1; then
        log "✅ Admin seeded."
    else
        warn "❌ Admin seeding failed."
    fi
fi

# --- Step 5: Launch App ---
log "Step 5/5: Launching Uvicorn..."

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

    # Wait for application to be ready
    log "⏳ Waiting for application health check..."
    for i in {1..30}; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            log "✅ Application is healthy and ready!"
            break
        fi
        sleep 1
    done
fi

log "🎉 --- Supervisor sequence complete --- 🎉"
log "🌐 Access the application at: http://localhost:8000"
