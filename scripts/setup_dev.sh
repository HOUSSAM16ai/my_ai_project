#!/bin/bash
set -e

echo "🔧 Bootstrapping Database Environment..."

# 1. Sanitize and Export URL (The Magic Step)
# This script (scripts/bootstrap_db.py) ensures DATABASE_URL is:
# - Safe (passwords encoded)
# - Correct Scheme (postgresql+asyncpg)
# - SSL Ready (ssl=require)
export DATABASE_URL=$(python3 scripts/bootstrap_db.py)

if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL could not be determined."
    exit 1
fi

echo "✅ URL Sanitized."

# 1.5 Verify Connection Fix (Prevent PgBouncer Crashes)
# We verify that statement_cache_size=0 is correctly applied
echo "🔍 Verifying Database Connection and PgBouncer Fix..."
python3 scripts/fix_duplicate_prepared_statement.py --verify || {
    echo "❌ Connection verification failed! The environment is not safe for migrations."
    echo "   Check 'scripts/fix_duplicate_prepared_statement.py' output above."
    exit 1
}

# 2. Run Migrations (Now Safe)
# We rely on migrations/env.py to pick up the sanitized DATABASE_URL from env
echo "🚀 Running Migrations..."
alembic upgrade head

# 3. Seed Admin
# This script also respects the sanitized DATABASE_URL and connect_args
echo "👤 Seeding Admin..."
python3 scripts/seed_admin.py

echo "✅ Setup Complete."

# 4. Start Application
echo "🌐 Starting Application Server..."
# Use exec to replace the shell process with Uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
