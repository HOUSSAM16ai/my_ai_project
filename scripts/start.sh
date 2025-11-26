#!/bin/bash
# Self-healing start script

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Environment Self-Healing ---
# Ensure a .env file exists to prevent startup failures.
if [ ! -f .env ]; then
  echo "INFO: .env file not found. Creating a default fallback."
  echo "DATABASE_URL=sqlite+aiosqlite:///./dev.db" > .env
  echo "SECRET_KEY=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" >> .env
  echo "ALLOWED_HOSTS=[\"*\"]" >> .env
  echo "ENVIRONMENT=development" >> .env
  echo "ADMIN_EMAIL=admin@cogniforge.com" >> .env
  echo "ADMIN_PASSWORD=secureadminpassword" >> .env
  echo "ADMIN_NAME=Admin" >> .env
fi

# --- CRITICAL FIX: Load Environment Variables ---
# Export the variables from .env so that subsequent scripts can see them.
echo "INFO: Exporting environment variables from .env file..."
export $(grep -v '^#' .env | xargs)

# --- Dependency Installation ---
echo "INFO: Installing Python dependencies..."
pip --cache-dir ./.pip_cache install -r requirements.txt > /dev/null

# --- Database Migration ---
echo "INFO: Running database migrations..."
alembic upgrade head

# --- Admin User Seeding ---
echo "INFO: Seeding admin user..."
python scripts/seed_admin.py

# --- Start Server ---
# Now, run the application using the standard ASGI entry point.
# The --reload flag is removed to ensure stability in automated environments.
echo "INFO: Starting Uvicorn server on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
