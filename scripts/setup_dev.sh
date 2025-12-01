#!/bin/bash
# This script provides a comprehensive setup for the development environment.
set -euo pipefail

print_header() {
    echo ""
    echo "--- $1 ---"
}

print_header "Phase 1: Installing Python Dependencies"
pip install -r requirements.txt

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

print_header "Phase 3: Handing over to The Guardian"
exec ./scripts/codespace_guardian.sh
