#!/bin/sh
# entrypoint.sh - v9.0 (The Final Ignition Protocol for the Web App)
set -e

# The 'migrations' service guarantees the world is built.
# This script's ONLY job is to ignite the Gunicorn server.
echo ">>> [WEB Entrypoint] The world is built. Igniting Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --user appuser --group appgroup "run:app"