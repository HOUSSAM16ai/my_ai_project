#!/bin/sh
# ai_service/entrypoint.sh - v6.0 (The Final Ignition Protocol for the AI Core)
set -e

# This script trusts the orchestration of docker-compose completely.
# Its only job is to ignite the Uvicorn server.
echo ">>> [AI Core] The world is built. Igniting Uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000