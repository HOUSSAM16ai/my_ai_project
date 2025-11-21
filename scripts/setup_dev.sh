#!/bin/bash
set -e

MARKER_FILE=".dev_ready"

if [ -f "$MARKER_FILE" ]; then
    echo "Environment already set up! 🚀"
    exit 0
fi

echo "🚀 Starting First-Time Setup..."

# 0. Check/Create .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    # Update DATABASE_URL to use SQLite for local dev by default to ensure immediate functionality
    # We use sed to replace the example postgres URL with the sqlite one.
    sed -i 's|^DATABASE_URL=.*|DATABASE_URL="sqlite+aiosqlite:///./test.db"|' .env
    echo "✅ .env created with SQLite default."
fi

# 1. Install Dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# 2. Run Migrations
echo "🔄 Running Smart Migrations..."
python scripts/smart_migrate.py

# 3. Seed Admin
echo "🌱 Seeding Admin User..."
python scripts/seed_admin.py

# 4. AI Service Check
echo "🤖 Checking AI Services Configuration..."
# Source .env to check variables in bash context
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

if [ -z "$OPENROUTER_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: No AI Service API Keys found (OPENROUTER_API_KEY / OPENAI_API_KEY)."
    echo "    Ensure they are set in your .env file or environment."
else
    echo "✅ AI Service Configuration detected."
fi

# 5. Create Marker
touch "$MARKER_FILE"
echo "✅ Setup Complete."

echo ""
echo "To start the server, run: uvicorn app.main:app --reload"
