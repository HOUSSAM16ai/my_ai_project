#!/usr/bin/env bash
###############################################################################
# on-start.sh (Superhuman Automation Edition)
#
# Executed every time the container starts.
# Responsibilities (Fully Automated & Idempotent):
#   1. Start background services (if any additional ones needed).
#   2. Ensure DB is ready.
#   3. Retry Migrations (if on-create failed).
#   4. Ensure Admin User.
###############################################################################

set -Eeuo pipefail
cd /app  # FORCE ROOT CONTEXT
source .devcontainer/utils.sh

trap 'err "An unexpected error occurred (Line $LINENO)."' ERR

log "🚀 On-Start: Launching the fully automated CogniForge ecosystem..."

# 1. Wait for the database to be ready
log "Step 1/3: Waiting for the database..."
if [ -n "${DATABASE_URL:-}" ]; then
    log "Checking database connection..."
    # Simple python check
    python3 -c "
import sys, time, os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

db_url = os.getenv('DATABASE_URL')
if not db_url: sys.exit(0)

engine = create_engine(db_url)
for i in range(30):
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        sys.exit(0)
    except OperationalError:
        time.sleep(2)
sys.exit(1)
" || err "Database not ready after waiting."
    ok "✅ Database is ready."
fi

# 2. Migrations (Retry/Ensure)
log "Step 2/3: Ensuring Database Schema..."
if command -v alembic &> /dev/null; then
    # VERIFY FILE
    if [ ! -f "alembic.ini" ]; then
        warn "WARNING: alembic.ini not found in $(pwd). Skipping migrations."
    else
        alembic upgrade head
        ok "✅ Database migrations applied."
    fi
fi

# 3. Create or update admin user
log "Step 3/3: Ensuring admin user exists..."
if [ -f "cli.py" ]; then
    # Try the create-admin command if it exists in the CLI structure
    if python cli.py --help | grep -q "create-admin"; then
         python cli.py create-admin || warn "Admin creation failed."
    else
         # Try 'users create-admin' or skip
         if python cli.py --help | grep -q "users"; then
             python cli.py users create-admin || warn "Admin creation failed."
         fi
    fi
fi

echo
log "🎉 --- System is fully operational --- 🎉"
