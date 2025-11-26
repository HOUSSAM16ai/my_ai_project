#!/usr/bin/env bash
set -euo pipefail

# 1) kill old uvicorn
pkill -f uvicorn || true
sleep 1

# 2) ensure .env exists (fallback)
if [ ! -f .env ]; then
  echo "PORT=8000" > .env
  echo "APP_ENV=development" >> .env
  # add other defaults as needed
fi

# 3) build frontend
if [ -d app/static ]; then
  echo "Building frontend..."
  pushd app/static
  if [ -f package-lock.json ]; then npm ci; else npm install; fi
  NODE_OPTIONS="--max-old-space-size=8192" npm run build
  popd
fi

# 4) run migrations (optional)
# alembic upgrade head || true

# 5) start backend
echo "Starting uvicorn..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload > uvicorn.log 2>&1 &
sleep 2

# 6) show status
ss -lntp | grep :${PORT:-8000} || true
tail -n 50 uvicorn.log || true

echo "Done. Open forwarded URL for port ${PORT:-8000}"
