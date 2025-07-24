# Version 2.0 - Simplified and Robust
FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install all necessary system dependencies
RUN apk update && \
    apk add --no-cache build-base postgresql-dev git bash postgresql-client netcat-openbsd

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make the entrypoint script executable (chmod +x)
RUN chmod +x /app/entrypoint.sh

EXPOSE 5000

# Set the entrypoint to our smart script
ENTRYPOINT ["/app/entrypoint.sh"]