#!/bin/bash
# scripts/codespace_guardian.sh
# The Ultimate Guardian for Port 8000
# Handles Cleanup, Start, Wait, Visibility, and Monitoring.

set -u

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[GUARDIAN]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 1. Environment & Path Verification
# Ensure we use the python that has the packages installed.
# We try to detect the venv or fallback to system python.
if [ -f ".venv/bin/python3" ]; then
    PYTHON_EXEC=".venv/bin/python3"
elif which python3 > /dev/null; then
    PYTHON_EXEC=$(which python3)
else
    error "No Python interpreter found!"
    exit 1
fi

log "Using Python: $PYTHON_EXEC"

# 2. Pre-flight Cleanup
./scripts/nuke_port_8000.sh

# 3. Start Server (Background)
log "Starting Uvicorn..."
$PYTHON_EXEC -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > uvicorn.log 2>&1 &
SERVER_PID=$!
log "Uvicorn started with PID: $SERVER_PID"

# 4. Wait for Port 8000 (The "Wait" Phase)
log "Waiting for Port 8000 to become active..."
MAX_RETRIES=30
COUNT=0
PORT_ACTIVE=0

while [ $COUNT -lt $MAX_RETRIES ]; do
    # Check if port is open using python itself (cross-platform reliable)
    if $PYTHON_EXEC -c "import socket; s=socket.socket(); s.settimeout(1); result=s.connect_ex(('0.0.0.0', 8000)); exit(result)" 2>/dev/null; then
        PORT_ACTIVE=1
        break
    fi

    # Check if process died early
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        error "Uvicorn process died during startup check!"
        cat uvicorn.log
        exit 1
    fi

    echo -n "."
    sleep 1
    COUNT=$((COUNT+1))
done
echo ""

if [ $PORT_ACTIVE -eq 1 ]; then
    success "Port 8000 is LISTENING."
else
    error "Timeout waiting for Port 8000."
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# 5. Set Visibility (The "Public" Phase)
# Only runs AFTER port is confirmed open.
if command -v gh &> /dev/null; then
    log "Setting Port 8000 visibility to PUBLIC..."
    # We retry this a few times because Codespaces API can be laggy
    for i in {1..5}; do
        if gh codespace ports visibility 8000:public; then
            success "Visibility set to PUBLIC."
            break
        else
            log "Visibility attempt $i failed. Retrying..."
            sleep 2
        fi
    done
else
    log "'gh' CLI not found. Skipping visibility (Manual forwarding may be required)."
fi

# 6. Monitor Loop (The "Self-Healing" Phase)
log "Entering Guardian Monitor Mode."
log "Tailing logs to stdout..."

# Trap signals to kill the server when this script is killed
trap "kill $SERVER_PID; exit" SIGINT SIGTERM

# We tail the log in the background to show output
tail -f uvicorn.log &
TAIL_PID=$!

wait $SERVER_PID
EXIT_CODE=$?

# If we get here, the server crashed or stopped.
error "Uvicorn exited with code $EXIT_CODE."
kill $TAIL_PID 2>/dev/null

# Restart Logic (Simple, not infinite loop to avoid madness)
log "Attempting ONE restart in 5 seconds..."
sleep 5
exec "$0" # Re-executes this script completely (fresh start)
