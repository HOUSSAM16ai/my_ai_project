#!/bin/bash
# scripts/setup_dev.sh — Simplified development setup
# This script installs dependencies and starts the server directly.

set -euo pipefail

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "⚙️  Configuring environment..."
if [ ! -f .env ]; then
  cat > .env <<EOF
DATABASE_URL=sqlite+aiosqlite:///./dev.db
SECRET_KEY=dev-secret
TESTING=1
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=password
ADMIN_NAME=AdminUser
EOF
  echo "Created default .env file"
fi

echo "🚀 Starting CogniForge..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
