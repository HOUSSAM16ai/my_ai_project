#!/bin/sh
# entrypoint.sh - The Supercharged Ignition Protocol v5.1 (UTF-8 Force)
set -e

# --- THE SUPERCHARGED FIX for ENCODING ---
# We are EXPORTING these environment variables. This tells ANY Python script
# that runs in this container to use UTF-8 as its default encoding for
# everything, from reading files to printing to the console.
# This is a more powerful and fundamental fix.
export PYTHONIOENCODING=UTF-8
export LANG=C.UTF-8

echo ">>> [IGNITION PROTOCOL] Awaiting PostgreSQL handshake on db:5432..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo ">>> [IGNITION PROTOCOL] Handshake successful. PostgreSQL core is online."

echo ">>> [IGNITION PROTOCOL] Synchronizing database schema to latest version..."
flask db upgrade

echo ">>> [IGNITION PROTOCOL] Igniting Gunicorn engine..."
echo ">>> [SECURITY PROTOCOL] Dropping privileges to 'appuser:appgroup'..."
echo ">>> [SYSTEM STATUS] All systems go. CogniForge is now online."
exec gunicorn --bind 0.0.0.0:5000 --user appuser --group appgroup "run:app"