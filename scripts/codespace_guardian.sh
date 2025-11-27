#!/usr/bin/env bash
set -euo pipefail
# Guardian: clean zombies, start dev server, wait for port, open visibility
BRANCH="fix/ui-whitepage-guardian"
PORT=8000
LOG=/tmp/jules_guardian.log

echo ">>> Starting Guardian at $(date)" | tee $LOG

# cleanup function
cleanup() {
  echo ">>> Cleanup: killing uvicorn/gunicorn processes" | tee -a $LOG
  pkill -f uvicorn || true
  pkill -f gunicorn || true
}
trap cleanup EXIT

# ensure no stale servers
cleanup

# start the dev server (use project's setup script if present)
if [ -f "./scripts/setup_dev.sh" ]; then
    ./scripts/setup_dev.sh || true
else
    # Fallback if setup_dev.sh doesn't exist
    export ENVIRONMENT=development
    export DATABASE_URL="sqlite+aiosqlite:///./test.db"
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT &
fi

# wait for port to be live (socket check)
python3 - <<PY
import socket, time, sys
for i in range(30):
    s = socket.socket()
    try:
        s.connect(("127.0.0.1", $PORT))
        print("port $PORT is ready")
        s.close()
        sys.exit(0)
    except Exception:
        time.sleep(1)
print("port check timed out", file=sys.stderr)
sys.exit(1)
PY

# Verify health endpoint
curl -sS http://127.0.0.1:$PORT/health | tee -a $LOG

# set codespace port visibility (if gh CLI available)
if command -v gh >/dev/null 2>&1; then
  gh codespace ports visibility $PORT:public --repo "${CODESPACE_REPO:-}" || true
fi

echo ">>> Guardian complete" | tee -a $LOG
