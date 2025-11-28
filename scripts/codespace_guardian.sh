#!/usr/bin/env bash
set -euo pipefail

# usage: scripts/codespace_guardian.sh [PORT]
PORT=${1:-8000}
BASE="http://127.0.0.1:$PORT"
MAX_RETRIES=30
SLEEP_TIME=2

echo "🛡️ Codespace Guardian Active on Port $PORT"

# 1. Wait for Server to be ready
echo "⏳ Waiting for server at $BASE..."
for ((i=1;i<=MAX_RETRIES;i++)); do
    if curl -s "$BASE/health" > /dev/null; then
        echo "✅ Server is UP."
        break
    fi
    echo "   ...retry $i/$MAX_RETRIES"
    sleep $SLEEP_TIME
done

# If still failed:
if ! curl -s "$BASE/health" > /dev/null; then
    echo "❌ Server failed to start within timeout."
    if [ -f "/tmp/uvicorn.log" ]; then
        echo "📜 Dumping /tmp/uvicorn.log (last 50 lines):"
        tail -n 50 /tmp/uvicorn.log
    fi
    exit 1
fi

# 2. Check Root HTML and Headers
echo "🔍 Checking Root (SPA) and Headers..."
HEADERS=$(mktemp)
BODY=$(mktemp)

# Use -D to dump headers to file, output body to another
curl -s -D "$HEADERS" -o "$BODY" "$BASE/"

# A. Verify HTML content (SPA is served)
if grep -q "<!doctype html>" "$BODY" || grep -q "<html" "$BODY"; then
    echo "✅ Root returns HTML."
else
    echo "❌ Root did NOT return HTML. Response start:"
    head -n 5 "$BODY"
    echo "📜 Headers:"
    cat "$HEADERS"
    exit 1
fi

# B. Verify Security Headers (Codespace Mode)
# We expect NO X-Frame-Options and NO frame-ancestors in CSP
FAILED=0

if grep -i "x-frame-options" "$HEADERS"; then
    echo "❌ FAIL: 'X-Frame-Options' header found! (Should be removed in dev)"
    FAILED=1
else
    echo "✅ 'X-Frame-Options' is absent."
fi

if grep -i "content-security-policy" "$HEADERS"; then
    CSP=$(grep -i "content-security-policy" "$HEADERS")
    if echo "$CSP" | grep -i "frame-ancestors"; then
        echo "❌ FAIL: 'frame-ancestors' found in CSP! (Should be removed/relaxed)"
        FAILED=1
    else
        echo "✅ CSP present but 'frame-ancestors' absent (Safe)."
    fi
else
    echo "✅ CSP absent (Acceptable for dev)."
fi

if [ $FAILED -eq 1 ]; then
    echo "📜 Full Headers Dump:"
    cat "$HEADERS"
    exit 2
fi

echo "🎉 All Systems Go: Codespace Preview should work!"
rm "$HEADERS" "$BODY"
exit 0
