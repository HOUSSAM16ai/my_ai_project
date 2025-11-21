#!/bin/bash
set -e

echo "🔧 Bootstrapping Database Environment..."

# 1. Sanitize and Export URL (The Magic Step)
export DATABASE_URL=$(python3 scripts/bootstrap_db.py)

if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL could not be determined."
    exit 1
fi

echo "✅ URL Sanitized."

# 1.5 Verify Connection Fix (Prevent PgBouncer Crashes)
echo "🔍 Verifying Database Connection and PgBouncer Fix..."
python3 scripts/fix_duplicate_prepared_statement.py --verify || {
    echo "❌ Connection verification failed! The environment is not safe for migrations."
    echo "   Check 'scripts/fix_duplicate_prepared_statement.py' output above."
    exit 1
}

# 2. Run Migrations (Now Safe)
echo "🚀 Running Migrations..."
alembic upgrade head

# 3. Seed Admin
echo "👤 Seeding Admin..."
python3 scripts/seed_admin.py

echo "✅ Setup Complete."
