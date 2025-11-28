#!/usr/bin/env bash
# scripts/codespace_guardian.sh
# Guardian script for CI/Codespaces readiness checks.
# Usage: ./scripts/codespace_guardian.sh [HOST] [PORT] [UVICORN_LOG]
# Defaults: HOST=127.0.0.1 PORT=8000 UVICORN_LOG=/tmp/uvicorn.log

set -euo pipefail

HOST="${1:-127.0.0.1}"
PORT="${2:-8000}"
UVICORN_LOG="${3:-/tmp/uvicorn.log}"

BASE="http://${HOST}:${PORT}"
HEALTH="${BASE}/health"
ROOT="${BASE}/"

MAX_ATTEMPTS=30
SLEEP_SECONDS=1

echo "[guardian] base=${BASE}"
echo "[guardian] waiting for ${HEALTH} (timeout ${MAX_ATTEMPTS}s total)..."

attempt=0
while [ $attempt -lt $MAX_ATTEMPTS ]; do
  attempt=$((attempt + 1))
  if curl -sS "$HEALTH" >/dev/null 2>&1; then
    echo "[guardian] /health OK (attempt $attempt)"
    break
  fi
  echo "[guardian] /health not ready (attempt $attempt/${MAX_ATTEMPTS})..."
  sleep $SLEEP_SECONDS
done

if [ $attempt -ge $MAX_ATTEMPTS ]; then
  echo "CRITICAL: /health did not become ready in time."
  echo "----- uvicorn log (tail 200) -----"
  test -f "$UVICORN_LOG" && tail -n 200 "$UVICORN_LOG" || echo "(no uvicorn log found at $UVICORN_LOG)"
  echo "-----------------------------------"
  # Dump curl info
  curl -I "$BASE/" || true
  curl -s "$BASE/" | head -c 500 || true
  exit 10
fi

echo "[guardian] fetching root ${ROOT} ..."
HTTP_CODE=$(curl -s -o /tmp/__guardian_root.html -w "%{http_code}" "$ROOT" || echo "000")

if [ "$HTTP_CODE" != "200" ]; then
  echo "FAIL: ${ROOT} returned HTTP ${HTTP_CODE} (expected 200)."
  echo "----- Response headers -----"
  curl -sI "$ROOT" || true
  echo "----- Response body excerpt (first 400 chars) -----"
  head -c 400 /tmp/__guardian_root.html || true
  echo "----- uvicorn log (tail 200) -----"
  test -f "$UVICORN_LOG" && tail -n 200 "$UVICORN_LOG" || true
  exit 11
fi

# Quick sanity for HTML (doctype or html tag)
if ! head -c 256 /tmp/__guardian_root.html | grep -qiE "<!doctype|<html"; then
  echo "FAIL: root returned 200 but does not look like HTML (may be JSON or error page)."
  head -n 200 /tmp/__guardian_root.html || true
  exit 12
fi

echo "[guardian] checking headers for framing issues..."

# Fetch headers once
curl -sI "$ROOT" > /tmp/__guardian_headers.txt || true

# 1) X-Frame-Options must NOT be present in dev/Codespaces preview
if grep -i '^x-frame-options:' /tmp/__guardian_headers.txt >/dev/null; then
  echo "FAIL: X-Frame-Options header present (will block embedding in iframe)."
  grep -i '^x-frame-options:' /tmp/__guardian_headers.txt || true
  echo "----- uvicorn log (tail 200) -----"
  test -f "$UVICORN_LOG" && tail -n 200 "$UVICORN_LOG" || true
  exit 13
else
  echo "PASS: No X-Frame-Options header."
fi

echo "[guardian] all checks passed."
exit 0
