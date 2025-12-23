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
# Optimization: Check if packages are already installed to avoid costly pip lookup
# pip freeze takes time, but less than install.
# Better strategy: Assume container is up to date, only install if strictly necessary.
# We run pip install but capture output to log and hope cache is hit.
if pip install --no-cache-dir -r requirements.txt >> "$LOG_FILE" 2>&1; then
    log "✅ Python dependencies verified."
else
    warn "Python dependency check had issues. See logs."
fi

# --- Step 2: Migrations ---
log "Step 2/4: Smart Migrations..."
if [ -f "scripts/smart_migrate.py" ]; then
    log "Executing smart_migrate.py..."
    if python scripts/smart_migrate.py >> "$LOG_FILE" 2>&1; then
        log "✅ Migrations completed successfully."
    else
        err "❌ Migrations failed. Application may not behave correctly."
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
    log "🚀 Executing scripts/start.sh..."

    # We use nohup here to ensure it stays alive independent of this script if needed,
    # though this script itself is backgrounded.
    # We redirect BOTH stdout and stderr to the log file.
    nohup bash scripts/start.sh >> "$LOG_FILE" 2>&1 &
    PID=$!
    log "✅ Uvicorn started with PID $PID. Logs are streaming to $LOG_FILE"
fi

log "🎉 --- Supervisor sequence complete --- 🎉"
