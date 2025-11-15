#!/usr/bin/env bash
###############################################################################
# on-create.sh (Superhuman Automation Edition)
#
# Executed only once when the container is created.
# Responsibilities:
#   1. Build all Docker services defined in docker-compose.yml.
###############################################################################

set -Eeuo pipefail
source .devcontainer/utils.sh

trap 'err "An unexpected error occurred (Line $LINENO)."' ERR

log "🚀 On-Create: Building Docker images for a fresh start..."

# Build all services. The --no-cache flag can be added for a cleaner build if needed.
docker-compose build

ok "✅ Docker images built successfully. The environment is ready for the first start."
echo
