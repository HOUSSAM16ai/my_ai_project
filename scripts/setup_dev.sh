#!/bin/bash
set -euo pipefail

# --- SETUP LOGGING ---
LOG_FILE=".setup_dev.log"
exec 3>&1 4>&2 # Save original stdout/stderr
exec > >(tee -a "$LOG_FILE") 2>&1 # Redirect all output to log file and stdout

echo "🔧 Starting Development Environment Setup..."
echo "📜 Logs will be saved to $LOG_FILE"

# --- 1. DEPENDENCIES ---
echo "📦 Installing Python Dependencies..."
pip install -r requirements.txt > /dev/null 2>&1 || { echo "❌ Pip install failed"; exit 1; }
echo "✅ Dependencies Installed."

# --- 2. BOOTSTRAP DATABASE URL ---
echo "🔗 Bootstrapping Database Connection..."
# Capture ONLY the stdout from bootstrap_db.py.
# stderr flows through to our script's stderr (and log file).
# We use a temporary file to avoid any subshell weirdness, although strict variable capture is also fine.
RAW_URL_FILE="/tmp/db_url_capture"
python3 scripts/bootstrap_db.py > "$RAW_URL_FILE"

# Read and Trim
DATABASE_URL=$(cat "$RAW_URL_FILE" | tr -d '\n' | tr -d ' ')
export DATABASE_URL

# Validation
if [[ -z "$DATABASE_URL" ]]; then
    echo "❌ Error: DATABASE_URL is empty. Bootstrap failed."
    exit 1
fi

if [[ "$DATABASE_URL" != *"://"* ]]; then
    echo "❌ Error: Invalid DATABASE_URL format: $DATABASE_URL"
    exit 1
fi

echo "✅ Database URL captured: ${DATABASE_URL//:*/:******@...}"

# --- 3. VERIFY ENGINE SAFETY ---
echo "🛡️  Verifying Engine Configuration..."
python3 scripts/fix_duplicate_prepared_statement.py --verify || {
    echo "❌ Engine verification failed. See logs above."
    exit 1
}

# --- 4. RUN MIGRATIONS ---
echo "🚀 Running Alembic Migrations..."
# Ensure we are at head
alembic upgrade head || {
    echo "❌ Migration failed."
    exit 1
}
echo "✅ Schema is up to date."

# --- 5. SEED DATA ---
echo "🌱 Seeding Admin User..."
python3 scripts/seed_admin.py || {
    echo "❌ Admin seeding failed."
    exit 1
}

# --- 6. VALIDATE TESTS (Smoke Test) ---
if [ -f "tests/conftest.py" ]; then
    echo "🧪 Running Smoke Tests..."
    # Running a quick check, not the full suite, to ensure env is viable
    pytest -q tests/transcendent/ --ignore=tests/transcendent/test_infrastructure_rebuild.py || echo "⚠️  Some smoke tests failed, but continuing setup..."
fi

echo "✅ Setup Complete! Run 'uvicorn app.main:create_app --factory --reload' to start."
