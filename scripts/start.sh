#!/bin/bash
set -e

# Load .env file if it exists (Crucial for local dev and Codespaces)
if [ -f .env ]; then
  echo "Loading environment from .env..."
  set -a
  source .env
  set +a
fi

# Standardized startup command using the Factory Pattern
# We use python3 -m uvicorn to ensure it uses the correct environment path
echo "🚀 Launching CogniForge Reality Kernel..."
exec python3 -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
