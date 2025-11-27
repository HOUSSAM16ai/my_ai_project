#!/usr/bin/env bash
set -euo pipefail
# usage: scripts/codespace_guardian.sh [PORT]
PORT=${1:-8000}
BASE="http://127.0.0.1:$PORT"
echo "Checking $BASE/health"
curl -fsS "$BASE/health" || (echo "health failed" >&2; exit 1)
echo "Fetching root HTML and headers..."
HEADERS=$(mktemp)
curl -si "$BASE/" > "$HEADERS"
grep -i 'x-frame-options' "$HEADERS" || echo "no X-Frame header"
grep -i 'content-security-policy' "$HEADERS" || echo "no CSP header"
# Validate that frame-ancestors is gone or relaxed
if grep -i 'frame-ancestors' "$HEADERS"; then
  echo "frame-ancestors still present — FAIL" >&2
  cat "$HEADERS" >&2
  exit 2
fi
echo "OK: iframe-blocking headers absent. Success."
