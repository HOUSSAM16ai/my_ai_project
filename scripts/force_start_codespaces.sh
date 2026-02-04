#!/bin/bash
# force_start_codespaces.sh
# Ensure Port 8000 is open, public, and stable.

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[AUTO-FIX]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log "Starting Deep Clean & Start Protocol for Port 8000..."

# 1. Kill any existing process on 8000
PID=$(lsof -t -i:8000)
if [ -n "$PID" ]; then
    log "Killing stuck process $PID on port 8000..."
    kill -9 $PID
else
    log "Port 8000 is clean."
fi

# 2. Ensure Visibility is Public
if command -v gh &> /dev/null; then
    log "Enforcing PUBLIC visibility for port 8000..."
    # Attempt to set visibility. This might fail if not in a Codespace or not auth'd, so we allow failure.
    if gh codespace ports visibility 8000:public; then
        success "Port 8000 visibility set to PUBLIC."
    else
        error "Could not set visibility via 'gh'. Is this a Codespace?"
    fi
else
    log "'gh' CLI not found. Skipping visibility enforcement."
fi

# 3. Start Server Loop
log "Starting Uvicorn with infinite auto-restart loop..."

while true; do
    echo "-----------------------------------------------------"
    log "Launching Server..."
    # Run uvicorn. If it crashes, the loop restarts it.
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

    EXIT_CODE=$?
    error "Server process exited with code $EXIT_CODE."
    log "Restarting in 3 seconds..."
    sleep 3
done
