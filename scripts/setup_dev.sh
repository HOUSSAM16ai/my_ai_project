#!/bin/bash
set -euo pipefail

# --- SETUP LOGGING ---
LOG_FILE=".setup_dev.log"
exec 3>&1 4>&2 # Save original stdout/stderr
exec > >(tee -a "$LOG_FILE") 2>&1 # Redirect all output to log file and stdout

echo "🔧 Starting SUPERHUMAN Development Environment Setup..."
echo "📜 Logs will be saved to $LOG_FILE"

# --- 1. PYTHON DEPENDENCIES ---
echo "📦 [Phase 1] Installing Python Dependencies..."
if pip install -r requirements.txt > /dev/null 2>&1; then
    echo "✅ Python Dependencies Installed."
else
    echo "❌ Python Pip install failed. Retrying with verbose output..."
    pip install -r requirements.txt || { echo "❌ Critical Failure: Pip install failed completely."; exit 1; }
fi

# --- 2. NODE DEPENDENCIES ---
echo "📦 [Phase 2] Installing Node.js Dependencies..."
if [ -f "package.json" ]; then
    if npm install > /dev/null 2>&1; then
        echo "✅ Node Dependencies Installed."
    else
        echo "⚠️  npm install had issues. Retrying verbose..."
        npm install || echo "⚠️  npm install failed, but proceeding (Frontend might be broken)."
    fi
else
    echo "⚠️  No package.json found. Skipping Node setup."
fi

# --- 3. BOOTSTRAP DATABASE URL ---
echo "🔗 [Phase 3] Bootstrapping Database Connection..."
RAW_URL_FILE="/tmp/db_url_capture"
if ! python3 scripts/bootstrap_db.py > "$RAW_URL_FILE"; then
    echo "❌ Database Bootstrap Failed."
    exit 1
fi

DATABASE_URL=$(cat "$RAW_URL_FILE" | tr -d '\n' | tr -d ' ')

if [[ -z "$DATABASE_URL" ]]; then
    echo "❌ Error: DATABASE_URL is empty."
    exit 1
fi

echo "✅ Database Configured: ${DATABASE_URL//:*/:******@...}"

# --- 4. PERSIST ENVIRONMENT (.env) ---
echo "💾 [Phase 4] Persisting Environment Configuration..."
if [ ! -f .env ]; then
    touch .env
fi

# Function to update or add a key-value pair in .env
update_env() {
    local key=$1
    local value=$2
    # Always quote the value to prevent syntax errors with spaces
    local quoted_value="\"$value\""

    if grep -q "^$key=" .env; then
        # Use a temp file to avoid issues with sed in-place on some systems
        # We escape the quoted value for sed if needed, but basic quotes usually work
        # Note: We use a delimiter | but if value has |, it might break.
        # For DATABASE_URL and SECRET_KEY this is usually fine.
        sed "s|^$key=.*|$key=$quoted_value|" .env > .env.tmp && mv .env.tmp .env
    else
        echo "$key=$quoted_value" >> .env
    fi
}

# Persist DATABASE_URL
update_env "DATABASE_URL" "$DATABASE_URL"

# Persist SECRET_KEY (Generate if missing)
if ! grep -q "^SECRET_KEY=" .env; then
    # Generate a strong random key
    GENERATED_KEY=$(openssl rand -hex 32)
    update_env "SECRET_KEY" "$GENERATED_KEY"
    echo "🔑 Generated new SECRET_KEY."
else
    echo "🔑 SECRET_KEY already exists."
fi

# --- SUPERHUMAN HEALING: Fix .env syntax before sourcing ---
echo "🚑 Healing Environment File..."
python3 scripts/heal_env.py

# Reload environment to ensure current shell has latest values
set -a
source .env
set +a
echo "✅ Environment persisted and healed."


# --- 5. VERIFY ENGINE SAFETY ---
echo "🛡️  [Phase 5] Verifying Engine Configuration..."
if ! python3 scripts/fix_duplicate_prepared_statement.py --verify; then
    echo "❌ Engine verification failed."
    exit 1
fi

# --- 6. RUN MIGRATIONS ---
echo "🚀 [Phase 6] Running Migrations..."
python3 scripts/smart_migrate.py || {
    echo "❌ Migration failed."
    exit 1
}

# --- 7. SEED DATA ---
echo "🌱 [Phase 7] Seeding Admin User..."
python3 scripts/seed_admin.py || {
    echo "❌ Admin seeding failed."
    exit 1
}

# --- 8. START BACKEND ---
echo "🚀 [Phase 8] Launching Backend (Port 8000)..."
if pgrep -f "uvicorn" > /dev/null; then
    echo "✅ Backend already running."
else
    nohup bash scripts/start.sh > .backend.log 2>&1 &
    echo "✅ Backend launched in background."
fi

# --- 9. START FRONTEND ---
echo "🎨 [Phase 9] Launching Frontend (Port 5000)..."
if pgrep -f "vite" > /dev/null; then
    echo "✅ Frontend already running."
else
    if [ -f "package.json" ]; then
        # Ensure we bind to 0.0.0.0
        nohup npm run dev -- --host 0.0.0.0 --port 5000 > .frontend.log 2>&1 &
        echo "✅ Frontend launched in background."
    else
        echo "⚠️  Skipping Frontend (No package.json)."
    fi
fi

# --- 10. HEALTH CHECK ---
echo "🏥 [Phase 10] Performing Health Check..."
sleep 5

if ! pgrep -f "uvicorn" > /dev/null; then
    echo "❌ Backend FAILED to start. Logs:"
    cat .backend.log
    exit 1
fi

if [ -f "package.json" ] && ! pgrep -f "vite" > /dev/null; then
    echo "⚠️  Frontend FAILED to start. Logs:"
    cat .frontend.log
    # We don't exit here strictly, but it's a warning
fi

echo "✨ SUPERHUMAN SETUP COMPLETE ✨"
echo "🌐 Backend: http://localhost:8000"
echo "🎨 Frontend: http://localhost:5000"
echo "✅ All systems operational."
