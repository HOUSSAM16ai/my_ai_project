#!/usr/bin/env bash
###############################################################################
# on-start.sh (Superhuman Automation Edition)
#
# Executed every time the container starts.
# Responsibilities (Fully Automated & Idempotent):
#   1. Start all Docker services in the background.
#   2. Wait for the database to be fully ready.
#   3. Run database migrations automatically.
#   4. Create or update the admin user from environment variables safely.
#   5. Display final status and instructions.
###############################################################################

set -Eeuo pipefail
source .devcontainer/utils.sh

trap 'err "An unexpected error occurred (Line $LINENO)."' ERR

log "🚀 On-Start: Launching the fully automated CogniForge ecosystem..."

# 1. Start all services detached
log "Step 1/4: Starting Docker services in the background..."
docker-compose up -d
ok "✅ Services are running."

# 2. Wait for the database to be ready
log "Step 2/4: Waiting for the database to become fully available..."
# We use docker-compose exec to run the wait-for-it script inside the 'web' container's network
MAX_TRIES=30
i=0
while ! docker-compose exec -T db pg_isready -U "postgres" -d "postgres" > /dev/null 2>&1; do
    i=$((i+1))
    if [ "$i" -ge "$MAX_TRIES" ]; then
        err "Database did not become ready in time. Aborting."
        exit 1
    fi
    echo "   - Waiting for database connection... ($i/$MAX_TRIES)"
    sleep 2
done
ok "✅ Database is ready to accept connections."

# 3. Run database migrations
log "Step 3/4: Automatically applying database migrations..."
docker-compose run --rm web flask db upgrade
ok "✅ Database migrations are up to date."

# 4. Create or update admin user (Idempotent and Safe)
log "Step 4/4: Ensuring admin user exists..."
if [ -z "${ADMIN_EMAIL:-}" ] || [ -z "${ADMIN_PASSWORD:-}" ]; then
    warn "⚠️ ADMIN_EMAIL or ADMIN_PASSWORD not set in environment."
    warn "   Skipping admin user creation. You can create one manually later:"
    warn "   docker-compose run --rm web flask users create-admin"
else
    # This command is now designed to be safe to run multiple times.
    # It will create the admin if it doesn't exist, or update the password if it does.
    docker-compose run --rm \
      -e ADMIN_EMAIL="${ADMIN_EMAIL}" \
      -e ADMIN_PASSWORD="${ADMIN_PASSWORD}" \
      -e ADMIN_NAME="${ADMIN_NAME:-Admin}" \
      web flask users create-admin --update-if-exists
    ok "✅ Admin user is configured."
fi

echo
log "🎉 --- System is fully operational --- 🎉"
log "Your application is running and accessible."
log "Happy coding!"
echo
