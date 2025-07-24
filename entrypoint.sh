#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait for the database to be ready
echo "Waiting for PostgreSQL to start..."
# 'db' is the service name of our database container
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL has started!"

# Create tables using the schema file
# We provide the password via an environment variable for security
echo "Initializing database tables..."
export PGPASSWORD=$POSTGPASSWORD
psql -h db -U $POSTGUSER -d $POSTGRES_DB -f /app/schema.sql

echo "Database initialized successfully."

# Start the main application
echo "Starting Gunicorn server..."
exec gunicorn --workers 1 --bind 0.0.0.0:5000 "app:app"