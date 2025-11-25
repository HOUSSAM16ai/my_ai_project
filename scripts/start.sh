#!/bin/bash
set -e

# --- SUPERHUMAN SELF-HEALING STARTUP SCRIPT ---

# 1. Environment Sanity Check & Self-Healing
if [ ! -f .env ]; then
  echo "⚠️ .env file not found. Creating a default one with SQLite."
  cat > .env <<EOL
# Default environment for local development
DATABASE_URL="sqlite+aiosqlite:///./db.sqlite3"
SECRET_KEY="a-very-secret-key-for-dev-only-change-in-prod"
# Add other essential variables here if needed
EOL
fi

# Load Environment
set -a
source .env
set +a

# 2. Explicitly set PYTHONPATH to the project root
export PYTHONPATH=${PYTHONPATH}:$(pwd)

# 3. Dependency Installation
echo "📦 Ensuring all dependencies are installed..."
pip install -r requirements.txt

# 4. Run Magic Access/Cleanup
# This script can perform pre-flight checks or cleanup operations.
python3 scripts/magic_access.py

# 5. Launch Application
echo "🚀 Igniting Reality Kernel V3..."

# Use python3 -m uvicorn for correct path resolution
# Bind to 0.0.0.0 to ensure external access in containers/codespaces
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
