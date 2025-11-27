#!/bin/bash
# This script runs a full verification suite for the application.
set -euo pipefail

echo "--- Running Ruff Lint Check ---"
ruff check .

echo "--- Running isort Check ---"
isort --check-only .

echo "--- Building Frontend ---"
(cd app/static && npm ci && NODE_OPTIONS="--max-old-space-size=8192" npm run build)

echo "--- Starting Server in Background ---"
export DATABASE_URL='sqlite+aiosqlite:///./test.db'
export SECRET_KEY='dev-secret-key'
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
SERVER_PID=$!

# Kill the server on script exit
trap 'kill $SERVER_PID' EXIT

# Wait for the server to start
sleep 5

echo "--- Checking Health Endpoint ---"
curl -f http://127.0.0.1:8000/health

echo "--- Verification Complete ---"
