#!/bin/bash
# This script provides a comprehensive setup for the development environment.
set -e

print_header() {
    echo ""
    echo "--- $1 ---"
}

print_header "Phase 1: Installing Dependencies"
pip install -r requirements.txt
npm install

print_header "Phase 2: Configuring Environment"
if [ ! -f .env ]; then
    SECRET_KEY=$(openssl rand -hex 32)
    echo "SECRET_KEY=${SECRET_KEY}" > .env
    echo "DATABASE_URL=sqlite+aiosqlite:///./dev.db" >> .env
    echo "ADMIN_EMAIL=admin@example.com" >> .env
    echo "ADMIN_PASSWORD=password" >> .env
    echo "ADMIN_NAME=AdminUser" >> .env
fi

print_header "Phase 3: Building Frontend (with increased memory)"
export NODE_OPTIONS="--max-old-space-size=8192"
npm run build
unset NODE_OPTIONS

print_header "Phase 4: Starting Application"
# Removed 'exec' to run as a subprocess
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
