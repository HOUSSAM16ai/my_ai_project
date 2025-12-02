#!/bin/bash
# This script provides a comprehensive setup for the development environment.
# It installs dependencies, configures environment, starts the server, and runs health checks.
set -euo pipefail

print_header() {
    echo ""
    echo "--- $1 ---"
}

cleanup() {
    # Kill background uvicorn process if it exists
    if [ -n "${UVICORN_PID:-}" ] && kill -0 "$UVICORN_PID" 2>/dev/null; then
        kill "$UVICORN_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

print_header "Phase 1: Installing Python Dependencies"
pip install -r requirements.txt

print_header "Phase 2: Configuring Environment"
if [ ! -f .env ]; then
  cat > .env <<EOF
DATABASE_URL=sqlite+aiosqlite:///./dev.db
SECRET_KEY=dev-secret
TESTING=1
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=password
ADMIN_NAME=AdminUser
EOF
fi

print_header "Phase 3: Starting Application Server (background)"
# Start uvicorn in background for health checks
UVICORN_LOG="/tmp/uvicorn.log"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$UVICORN_LOG" 2>&1 &
UVICORN_PID=$!
echo "[setup_dev] uvicorn started with PID $UVICORN_PID"

# Wait for server to initialize
sleep 3

print_header "Phase 4: Running Guardian Health Checks"
if ./scripts/codespace_guardian.sh 127.0.0.1 8000 "$UVICORN_LOG"; then
    echo "[setup_dev] Health checks passed!"
else
    GUARDIAN_EXIT=$?
    echo "[setup_dev] Health checks failed with exit code $GUARDIAN_EXIT"
    exit $GUARDIAN_EXIT
fi

# Stop background uvicorn before starting foreground version
kill "$UVICORN_PID" 2>/dev/null || true
unset UVICORN_PID
sleep 1

print_header "Phase 5: Running Server in Foreground (with --reload)"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
