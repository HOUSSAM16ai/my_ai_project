# Stage 1: Builder
FROM python:3.12-slim-bookworm as builder

WORKDIR /app

# Performance optimizations
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install dependencies into a user-local directory to easily copy later
# or install strictly to site-packages.
# Using --user or target prefix might be cleaner, but standard install to system python in builder is fine
# as we copy site-packages.
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final Runtime
FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1
# Ensure /app is in PYTHONPATH so absolute imports work
ENV PYTHONPATH="/app:$PYTHONPATH"

# Install runtime system dependencies
# libpq-dev is needed for asyncpg/psycopg2
# git/curl/procps are needed for VS Code extensions & health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    procps \
    iproute2 \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY . .

# Grant permissions
RUN chown -R appuser:appuser /app

# Set default user (can be overridden by devcontainer.json remoteUser: root)
# In production, this runs as appuser.
# In Codespaces, devcontainer.json overrides this to root (usually).
USER appuser

# Standard port
EXPOSE 8000

# Run Uvicorn targetting the exposed app instance
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
