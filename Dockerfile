# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /app

# Performance optimizations
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Install build dependencies
# Use cache mount to prevent re-downloading apt indexes
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY constraints.txt .
# Use cache mount for pip to persist downloads
# OPTIMIZATION: Install CPU-only torch first to prevent downloading 2GB+ CUDA wheels
# This fixes "Codespaces not launching" due to timeout/storage exhaustion
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements.txt -c constraints.txt

# Stage 2: Final Runtime
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
# Ensure /app is in PYTHONPATH so absolute imports work
ENV PYTHONPATH="/app:$PYTHONPATH"

# Install runtime system dependencies
# libpq-dev is needed for asyncpg/psycopg2
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    procps \
    iproute2 \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY . .

# Grant permissions
RUN chown -R appuser:appuser /app

# Set default user (can be overridden by devcontainer)
USER appuser

# Standard port
EXPOSE 8000

# Run Uvicorn targetting the exposed app instance
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
