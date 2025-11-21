#!/bin/bash
echo "🔧 Bootstrapping Database Environment..."

# 1. Sanitize and Export URL (The Magic Step)
export DATABASE_URL=$(python3 scripts/bootstrap_db.py)
echo "✅ URL Sanitized."

# 2. Run Migrations (Now Safe)
echo "🚀 Running Migrations..."
alembic upgrade head

# 3. Seed Admin
echo "👤 Seeding Admin..."
python3 scripts/seed_admin.py

echo "✅ Setup Complete."
