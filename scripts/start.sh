#!/bin/bash
set -e

# --- SUPERHUMAN STARTUP SCRIPT ---

# 1. Load Environment
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# 2. Run Magic Access/Cleanup
python3 scripts/magic_access.py

# 3. Launch Application
echo "🚀 Igniting Reality Kernel V3..."

# Use python3 -m uvicorn for correct path resolution
# Bind to 0.0.0.0 to ensure external access in containers
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
