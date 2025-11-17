# Stage 1: The Builder
# Use the full bullseye image to build dependencies, ensuring all build tools are available.
FROM python:3.12-bullseye AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a wheelhouse for the Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# Stage 2: The Final Image
# Use the slim version of the bullseye image for a smaller final footprint.
FROM python:3.12-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install only necessary runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the pre-built wheels from the builder stage and install them
COPY --from=builder /app/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt

# Copy the application code
COPY . .

# Set the port the application will run on
ENV PORT=5000

# Expose the port
EXPOSE ${PORT}

# Healthcheck to ensure the application is running correctly
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:${PORT}/health || exit 1

# Command to run the application using Gunicorn with Uvicorn workers
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", \
     "-w", "4", "--threads", "2", "--bind", "0.0.0.0:5000", \
     "--timeout", "120", "--keep-alive", "5"]
