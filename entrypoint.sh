#!/bin/sh

# Wait for the database to be ready
echo "Waiting for PostgreSQL..."

# The 'db' here is the service name from docker-compose.yml
while ! nc -z db 5432; do
  sleep 0.1
done

echo "PostgreSQL started"

# Run the Flask application
# We use exec to replace the shell process with the gunicorn process
exec gunicorn --workers 1 --bind 0.0.0.0:5000 "app:app"