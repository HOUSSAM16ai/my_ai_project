#!/bin/bash
# scripts/setup_dev.sh — Manual Development Helper
#
# NOTE: This script is NO LONGER automatically executed on attach.
# Run it manually if you need to reset/re-install the environment interactively.

set -euo pipefail

echo "⚠️  NOTE: The environment should already be running via the Superhuman Supervisor."
echo "    Check logs: tail -f .superhuman_bootstrap.log"
echo ""
read -p "Do you want to force a re-install and restart of the server? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "⚙️  Configuring environment..."
if [ ! -f .env ]; then
  echo "Generating .env..."
  cp .env.example .env || touch .env
fi

echo "🚀 Restarting CogniForge..."
# Kill existing uvicorn if running
pkill -f uvicorn || true
sleep 1
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
