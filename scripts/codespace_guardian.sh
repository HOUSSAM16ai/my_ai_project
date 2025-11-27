#!/usr/bin/env bash
set -e

# 1) Start server in background
export ENVIRONMENT=development
# We use uvicorn directly or the project's start script.
# Assuming uvicorn app.main:app is the standard way.
# Adding reload for development.
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

SERVER_PID=$!

# 2) Verify Health
echo "Waiting for server to start..."
sleep 5

if curl -sS -f http://127.0.0.1:8000/health >/dev/null; then
  echo "HEALTH OK"
else
  echo "HEALTH FAILED"
  kill $SERVER_PID || true
  exit 1
fi

# 3) Ensure X-Frame-Options is ABSENT
if curl -sI http://127.0.0.1:8000 | grep -i 'x-frame-options'; then
  echo "WARNING: x-frame-options still present"
else
  echo "SUCCESS: X-Frame-Options removed"
fi

# 4) Ensure CSP allows framing
if curl -sI http://127.0.0.1:8000 | grep -i 'content-security-policy' | grep -i 'frame-ancestors *'; then
  echo "SUCCESS: CSP frame-ancestors * present"
else
  echo "WARNING: CSP might restrict framing (check output)"
  curl -sI http://127.0.0.1:8000 | grep -i 'content-security-policy' || echo "No CSP found (which is also OK for framing usually)"
fi

# Keep process running
wait $SERVER_PID
