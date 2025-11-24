#!/usr/bin/env bash
###############################################################################
# on-start.sh (Superhuman Automation Edition - Non-Blocking)
#
# Executed every time the container starts.
#
# CHANGE: This script now delegates all heavy lifting to 'scripts/launch_stack.sh'
# and exits IMMEDIATELY. This solves the "Codespaces Stuck" issue where the
# lifecycle hook waits for foreground processes.
###############################################################################

set -Eeuo pipefail
cd /app  # FORCE ROOT CONTEXT
source .devcontainer/utils.sh

trap 'err "An unexpected error occurred (Line $LINENO)."' ERR

log "🚀 On-Start: Initializing Superhuman Supervisor..."

# Check if the supervisor script exists
if [ ! -f "scripts/launch_stack.sh" ]; then
    err "Critical: scripts/launch_stack.sh not found!"
    exit 1
fi

# Launch the full stack in the background
# We redirect all output to .superhuman_bootstrap.log
nohup bash scripts/launch_stack.sh > .superhuman_bootstrap.log 2>&1 &
PID=$!

ok "✅ Background Bootstrap Initiated (PID: $PID)."
log "📝 logs: tail -f .superhuman_bootstrap.log"
log "⚡ The environment is now interactive. The app will appear on port 8000 shortly."

# Exit immediately to unblock the IDE
exit 0
