# Version 1.3 - Professional Entrypoint Setup
FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies needed for the app and the entrypoint script
# netcat-openbsd provides the 'nc' command
# postgresql-client provides the 'psql' command
RUN apk update && \
    apk add --no-cache build-base postgresql-dev git bash postgresql-client netcat-openbsd

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Make the entrypoint script executable (this is the chmod +x step)
RUN chmod +x /app/entrypoint.sh

EXPOSE 5000

# The CMD is now handled by the entrypoint, but it's good practice to have it here
# for documentation or if someone runs the container without docker-compose.
CMD ["/app/entrypoint.sh"]