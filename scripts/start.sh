#!/bin/bash
set -e

# --- SUPERHUMAN STARTUP SCRIPT ---

# 1. Environment Bootstrap (Self-Healing)
if [ ! -f .env ]; then
  echo "--- Creating default .env file ---"
  echo "DATABASE_URL=sqlite+aiosqlite:///./default.db" > .env
  echo "SECRET_KEY=super-secret-key-for-development" >> .env
  echo "ENVIRONMENT=development" >> .env
  echo "--- .env created ---"
fi

# 2. Load Environment
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Run Magic Access/Cleanup
python3 scripts/magic_access.py

# 3. Launch Application
echo "🚀 Igniting Reality Kernel V3..."

# Use python3 -m uvicorn for correct path resolution
# Bind to 0.0.0.0 to ensure external access in containers
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
