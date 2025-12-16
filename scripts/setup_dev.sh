#!/bin/bash
# scripts/setup_dev.sh — Superhuman Development Setup (Restored)
# Handles dependencies, secrets, port visibility, and auto-restart.

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[SETUP]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

log "🚀 Initializing CogniForge Environment..."

# 1. Install Dependencies
log "📦 Verifying dependencies..."
if pip install -r requirements.txt > /dev/null 2>&1; then
    success "Dependencies installed."
else
    log "⚠️  Dependency check failed (check logs)."
fi

# 2. Configure Environment (Secrets)
if [ ! -f .env ]; then
  log "⚠️  .env not found. Generating defaults..."
  cat > .env <<EOF
DATABASE_URL=sqlite+aiosqlite:///./dev.db
SECRET_KEY=dev-secret
TESTING=1
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=password
ADMIN_NAME=AdminUser
EOF
  success "Created default .env file."
else
  success "Found existing .env configuration."
fi

# 3. Enforce Public Visibility (The "Magic" Fix)
log "🔓 Enforcing Public Port Visibility..."
if command -v gh &> /dev/null; then
    # We ignore errors here because we might not be authenticated or in a codespace
    if gh codespace ports visibility 8000:public 2>/dev/null; then
        success "Port 8000 is now PUBLIC. Browser should open automatically."
    else
        log "⚠️  Could not set visibility (not in Codespace or 'gh' not auth'd). Skipping."
    fi
else
    log "⚠️  'gh' CLI not found. Skipping visibility."
fi

# 4. Kill Stale Processes
PID=$(lsof -t -i:8000 || true)
if [ -n "$PID" ]; then
    log "🧹 Killing stale process on port 8000 (PID $PID)..."
    kill -9 $PID || true
fi

# 5. Start Server Loop
log "🔥 Starting Uvicorn (Auto-Restart Mode)..."
echo "-----------------------------------------------------"
echo "Admin Login: admin@example.com / password"
echo "-----------------------------------------------------"

while true; do
    # We use '|| true' to prevent 'set -e' from exiting the script if uvicorn crashes
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload || true
    log "⚠️  Server stopped. Restarting in 3s..."
    sleep 3
done
