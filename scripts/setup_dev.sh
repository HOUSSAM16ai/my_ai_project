#!/bin/bash
# This script provides a comprehensive setup for the development environment.
set -euo pipefail

print_header() {
    echo ""
    echo "--- $1 ---"
}

print_header "Phase 1: Installing Dependencies"
pip install -r requirements.txt
npm install

print_header "Phase 2: Configuring Environment"
if [ ! -f .env ]; then
  cat > .env <<EOF
DATABASE_URL=sqlite+aiosqlite:///./dev.db
SECRET_KEY=dev-secret
TESTING=1
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=password
ADMIN_NAME=AdminUser
EOF
fi

print_header "Phase 3: Building Frontend (with increased memory)"
export NODE_OPTIONS="--max-old-space-size=8192"
npm run build
unset NODE_OPTIONS

print_header "Phase 4: Starting Application"
# Removed 'exec' to run as a subprocess
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
