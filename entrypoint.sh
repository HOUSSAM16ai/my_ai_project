#!/bin/sh
# Exit immediately if a command exits with a non-zero status.
set -e

# Wait for the database container to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started!"

# Set the password for psql from the environment variable
export PGPASSWORD=$POSTGRES_PASSWORD

# Initialize the database tables
echo "Initializing database tables..."
psql -h db -U $POSTGRES_USER -d $POSTGRES_DB -f /app/schema.sql

echo "Database initialized."

# Start the main application
echo "Starting Gunicorn server..."
exec gunicorn --workers 1 --bind 0.0.0.0:5000 "app:app"