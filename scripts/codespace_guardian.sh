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
  echo "WARN: root returned 200 but does not look like HTML (may be JSON or error page)."
  head -n 200 /tmp/__guardian_root.html || true
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
  exit 12
else
  echo "PASS: No X-Frame-Options header."
fi

# 2) Content-Security-Policy analysis (flexible)
CSP_LINE=$(grep -i '^content-security-policy:' /tmp/__guardian_headers.txt || true)
if [ -z "$CSP_LINE" ]; then
  echo "Note: No CSP header returned — acceptable for dev preview (but consider explicit permissive CSP for preview)."
else
  # Normalize lowercase for checks
  CSP_LOWER=$(echo "$CSP_LINE" | tr '[:upper:]' '[:lower:]')
  echo "CSP header found: ${CSP_LINE}"

  # If frame-ancestors 'none' => fail
  if echo "$CSP_LOWER" | grep -q "frame-ancestors[^;]*'none'"; then
    echo "FAIL: CSP contains frame-ancestors 'none' which forbids framing."
    exit 13
  fi

  # If frame-ancestors contains only 'self' (and preview origin differs) -> WARN
  # We conservatively WARN because Codespaces preview origin is different
  if echo "$CSP_LOWER" | grep -q "frame-ancestors[^;]*'self'"; then
    echo "WARN: CSP frame-ancestors includes 'self' — this may block Codespaces preview (origin differs)."
    # do NOT fail automatically; make it configurable if you want strictness
  fi

  # If frame-ancestors present and not 'none' -> assume ok (log it)
  if echo "$CSP_LOWER" | grep -q "frame-ancestors"; then
    echo "PASS: CSP contains a frame-ancestors directive (not 'none'). Manual check recommended for allowed origins."
  else
    echo "Note: CSP present but no frame-ancestors directive — typically allows framing (unless other directives block resources)."
  fi
fi

# Optional: check that index.html contains at least one bundled JS file (simple heuristic)
if head -n 400 /tmp/__guardian_root.html | grep -Eo "<script[^>]+src=[\"']?([^\"' >]+)[\"']?" >/dev/null; then
  echo "PASS: index.html contains <script src=...> (bundle likely present)."
else
  echo "WARN: index.html does not contain script tags in the preview excerpt — check build output."
  # do not fail; only warn because SPA could be inline or bootstrapped differently
fi

echo "[guardian] all checks passed (or warnings shown)."
exit 0
