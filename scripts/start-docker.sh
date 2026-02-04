#!/bin/bash
set -e

echo "🚀 Starting CogniForge in Docker..."

# Run migrations
echo "📦 Running migrations..."
python -m alembic upgrade head 2>/dev/null || echo "⚠️ Migrations skipped (SQLite)"

# Start uvicorn
echo "✅ Starting Uvicorn..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
