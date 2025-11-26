#!/bin/bash
set -e

# --- Environment Setup ---
if [ ! -f .env ]; then
  echo "🔑 .env file not found. Creating one with default values for Codespaces."
  echo "SECRET_KEY='a-very-long-and-random-string-please-change-me-for-production'" > .env
  echo "DATABASE_URL='sqlite+aiosqlite:///./dev.db'" >> .env
  echo "VITE_ENABLE_SW=false" >> .env
fi

# Export environment variables for the current session
set -a
source .env
set +a

# --- Frontend Build ---
echo "📦 Installing frontend dependencies..."
npm --prefix . install

echo "🏗️ Building frontend..."
NODE_OPTIONS="--max-old-space-size=8192" npm --prefix . run build

echo "📄 Listing build artifacts..."
ls -l app/static/dist

# --- Backend Setup & Start ---
echo "🐍 Installing backend dependencies..."
pip install -r requirements.txt

echo "🚀 Starting backend server in the background..."
pkill -f "uvicorn app.main:app" || true
bash scripts/start-backend.sh &> backend.log 2>&1 &

echo "⏳ Waiting for backend to start..."
sleep 30

# --- Verification ---
echo "🔎 Running verification script..."
python scripts/verify_frontend.py

echo "✅ All steps completed successfully."
