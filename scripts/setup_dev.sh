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
# We use a temporary file to avoid any subshell weirdness.
RAW_URL_FILE="/tmp/db_url_capture"

# Run bootstrap with error handling
if ! python3 scripts/bootstrap_db.py > "$RAW_URL_FILE"; then
    echo "❌ Database Bootstrap Failed."
    echo "💡 Suggestion: Check if your database container is running (docker ps) and healthy."
    exit 1
fi

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
if ! python3 scripts/fix_duplicate_prepared_statement.py --verify; then
    echo "❌ Engine verification failed. See logs above."
    echo "💡 This usually means the database is reachable but rejected the connection (e.g., auth error or SSL issue)."
    exit 1
fi

# --- 4. RUN MIGRATIONS ---
echo "🚀 Running Alembic Migrations (via Smart Strategy)..."
# Use smart_migrate.py which includes timeout and retry logic
python3 scripts/smart_migrate.py || {
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

# --- 6. START APPLICATION ---
echo "🚀 Starting Application via standardized script..."

# Check if port 8000 is already in use by another process not named uvicorn
if lsof -i :8000 > /dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use."
    # We don't exit, we just warn, as it might be a previous instance or something else.
fi

if pgrep -f "uvicorn" > /dev/null; then
    echo "✅ Application is already running."
else
    echo "🚀 Starting Application in background..."
    # Ensure start.sh runs with nohup and detaches completely
    nohup bash scripts/start.sh > .app_background.log 2>&1 &

    # Superhuman verification: Wait a moment and check if it died immediately
    sleep 5
    if ! pgrep -f "uvicorn" > /dev/null; then
        echo "❌ Application failed to start. Logs:"
        cat .app_background.log
        exit 1
    fi
    echo "✅ Application started. Logs are being written to .app_background.log"
    echo "🌐 Access the app at http://localhost:8000"
fi
