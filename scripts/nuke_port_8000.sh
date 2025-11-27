#!/bin/bash
# scripts/nuke_port_8000.sh
# Aggressively cleans port 8000 and kills zombie python processes.

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[CLEANER]${NC} $1"; }
warn() { echo -e "${RED}[CLEANER]${NC} $1"; }

log "Initiating Deep Clean Protocol..."

# 1. Kill by Port (using lsof)
PIDS=$(lsof -t -i:8000)
if [ -n "$PIDS" ]; then
    log "Found processes on port 8000: $PIDS"
    kill -15 $PIDS 2>/dev/null
    sleep 2
    kill -9 $PIDS 2>/dev/null
    log "Port 8000 cleared."
else
    log "Port 8000 appears free."
fi

# 2. Kill by Name (uvicorn) - Prevent duplicates
# We grep for 'uvicorn' but exclude the grep itself and this script
UVICORN_PIDS=$(ps aux | grep "uvicorn" | grep -v "grep" | awk '{print $2}')
if [ -n "$UVICORN_PIDS" ]; then
    warn "Found stray Uvicorn processes: $UVICORN_PIDS"
    kill -9 $UVICORN_PIDS 2>/dev/null
    log "Stray Uvicorn processes nuked."
fi

# 3. Kill Zombie Parents (optional, but good for cleanup if we know the parent)
# For now, we trust that killing the main uvicorn process handles children or they get adopted by init.

# 4. Remove temporary lock files if any (app specific)
rm -f .uvicorn.pid

log "Deep Clean Complete."
